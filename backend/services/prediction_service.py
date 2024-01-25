from typing import List
from json import loads

from backend.core.celery_worker import async_make_batch_predictions
from backend.repository.prediction_repository import PredictionRepository
from backend.schema.prediction_schema import PredictionBatchInfo, PredictionInfo
from backend.schema.prediction_schema import PredictionFeatures, PredictionTarget, PredictionsReport
from backend.services.base_service import BaseService



def make_prediction(model, data): 
    answer = model.predict(data)
    return answer.tolist()


class PredictionService(BaseService):

    def __init__(self, prediction_repository: PredictionRepository):
        super().__init__(prediction_repository)
        self.prediction_repository = prediction_repository

    @staticmethod
    def make_batch_prediction(model_name, prediction_requests: List[dict]):
    
        async_result = async_make_batch_predictions.delay(model_name, prediction_requests)
        return async_result 

    def save_batch_prediction(self, user_id: int, model_name: str, transaction_id: int, batch_requests: List[dict], prediction_results: List[int]):
        batch = self.prediction_repository.create_batch(user_id=user_id, predictor_name=model_name,
                                                        transaction_id=transaction_id)
        
        for i in range(len(prediction_results)):
            prediction_data = batch_requests[i]
            prediction_data['batch_id'] = batch.id
            prediction_data['answer'] = prediction_results[i]
            self.prediction_repository.create_prediction(prediction_data)
        
        return batch

    def get_prediction_history(self, user_id: int) -> List[PredictionBatchInfo]:
        prediction_batches = self.prediction_repository.get_prediction_history(user_id)
        result = []

        for batch in prediction_batches:
            prediction_infos = []
            for prediction in batch.predictions:
                # category_label = _CATEGORY_LABEL_MAP.get(prediction.category_id, "Unknown Category")

                prediction_info = PredictionInfo(
                    features=PredictionFeatures(
                        N_Days=prediction.N_Days,
                        Drug=prediction.Drug,
                        Age=prediction.Age,
                        Sex=prediction.Sex,
                        Ascites=prediction.Ascites,
                        Hepatomegaly=prediction.Hepatomegaly,
                        Spiders=prediction.Spiders,
                        Edema=prediction.Edema,
                        Bilirubin=prediction.Bilirubin,
                        Cholesterol=prediction.Cholesterol,
                        Albumin=prediction.Albumin,
                        Copper=prediction.Copper,
                        Alk_Phos=prediction.Alk_Phos,
                        SGOT=prediction.SGOT,
                        Tryglicerides=prediction.Tryglicerides,
                        Platelets=prediction.Platelets,
                        Prothrombin=prediction.Prothrombin,
                        Stage=prediction.Stage,
                    ),
                    target=PredictionTarget(
                        answer=prediction.answer,
                    )
                )
                prediction_infos.append(prediction_info)

            model_name = batch.predictor.name
            transaction_amount = batch.transaction.amount if batch.transaction else 0
            timestamp = batch.created_at

            prediction_batch_info = PredictionBatchInfo(
                id=batch.id,
                predictions=prediction_infos,
                model_name=model_name,
                cost=transaction_amount,
                timestamp=timestamp
            )
            result.append(prediction_batch_info)

        return result

    def get_predictions_reports(self):
        raw_reports = self.prediction_repository.get_predictions_reports()
        predictions_reports = [PredictionsReport(model_name=model_name, total_prediction_batches=total_predictions)
                               for model_name, total_predictions in raw_reports]
        return predictions_reports
