from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from backend.core.container import Container
from backend.core.dependencies import get_current_user_payload
from backend.core.exceptions import PredictionError, ValidationError
from backend.schema.auth_schema import Payload
from backend.schema.prediction_schema import PredictionRequest, PredictionBatchInfo, PredictionInfo, \
    PredictionTarget, PredictionFeatures
from backend.schema.predictor_schema import PredictorInfo
from backend.services.billing_service import BillingService
from backend.services.prediction_service import PredictionService
from backend.services.predictor_service import PredictorService
from backend.utils.date import get_now
from backend.logger import LOGGER

router = APIRouter(
    prefix="/prediction",
    tags=["prediction"],
)

@router.get("/", response_model=List[PredictorInfo])
@inject
async def init_available_predictors(
        predictor_service: PredictorService = Depends(Provide[Container.predictor_service])
):
    available_models = predictor_service.init_predictors()
    return available_models

@router.get("/models", response_model=List[PredictorInfo])
@inject
async def get_available_models(
        predictor_service: PredictorService = Depends(Provide[Container.predictor_service])
):
    available_models = predictor_service.get_available_models()
    return available_models


@router.get("/history", response_model=List[PredictionBatchInfo])
@inject
async def get_prediction_history(
        current_user_payload: Payload = Depends(get_current_user_payload),
        prediction_service: PredictionService = Depends(Provide[Container.prediction_service])
):
    prediction_history = prediction_service.get_prediction_history(current_user_payload.id)
    return prediction_history


@router.post("/make", response_model=PredictionBatchInfo)
@inject
async def make_predictions(
        prediction_request: PredictionRequest,
        current_user_payload: Payload = Depends(get_current_user_payload),
        prediction_service: PredictionService = Depends(Provide[Container.prediction_service]),
        predictor_service: PredictorService = Depends(Provide[Container.predictor_service]),
        billing_service: BillingService = Depends(Provide[Container.billing_service])
):
    if len(prediction_request.features) == 0:
        raise ValidationError("No features provided")
    model_cost_per_prediction = predictor_service.get_model_cost(prediction_request.model_name)
    total_cost = model_cost_per_prediction * len(prediction_request.features)
    if not billing_service.reserve_funds(current_user_payload.id, total_cost):
        raise PredictionError(detail="Insufficient funds for prediction batch.")

    try:
        LOGGER.error("Prediction request: %s", prediction_request.features)
        # print(prediction_request.features)
        batch_requests = [
            {
                'N_Days': single_request.N_Days,
                'Drug': single_request.Drug,
                'Age': single_request.Age,
                'Sex': single_request.Sex,
                'Ascites': single_request.Ascites,
                'Hepatomegaly': single_request.Hepatomegaly,
                'Spiders': single_request.Spiders,
                'Edema': single_request.Edema,
                'Bilirubin': single_request.Bilirubin,
                'Cholesterol': single_request.Cholesterol,
                'Albumin': single_request.Albumin,
                'Copper': single_request.Copper,
                'Alk_Phos': single_request.Alk_Phos,
                'SGOT': single_request.SGOT,
                'Tryglicerides': single_request.Tryglicerides,
                'Platelets': single_request.Platelets,
                'Prothrombin': single_request.Prothrombin,
                'Stage': single_request.Stage
            }
            for single_request in prediction_request.features
        ]
        batch_result = prediction_service.make_batch_prediction(
            prediction_request.model_name,
            batch_requests
        )
        prediction_results = batch_result.get(timeout=30)  # loop inside

        predictions = []
        for i, result in enumerate(prediction_results):
            predictions.append(PredictionInfo(
                features=PredictionFeatures(**batch_requests[i]),
                target=PredictionTarget(answer=result)
            ))
    except ValueError as e:
        billing_service.cancel_reservation(current_user_payload.id, total_cost)
        raise PredictionError(detail=str(e))
    except Exception as e:
        billing_service.cancel_reservation(current_user_payload.id, total_cost)
        raise PredictionError(detail="An error occurred during prediction: " + str(e))
    try:
        transaction = billing_service.finalize_transaction(current_user_payload.id, total_cost)
        batch = prediction_service.save_batch_prediction(user_id=current_user_payload.id,
                                                         model_name=prediction_request.model_name,
                                                         transaction_id=transaction.id,
                                                         batch_requests = batch_requests,
                                                         prediction_results=prediction_results)

        return PredictionBatchInfo(
            id=batch.id,
            model_name=prediction_request.model_name,
            predictions=predictions,
            timestamp=get_now(),
            cost=total_cost
        )
    except Exception as e:
        raise PredictionError(detail=str(e))
