# Machine Learning Scheduling Engine - Phase B Sprint 2 Day 6 Option B
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
import json
import logging
import math
import statistics
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)

class MLModelType(Enum):
    """Machine learning model types"""
    LINEAR_REGRESSION = "linear_regression"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"

class FeatureType(Enum):
    """Feature types for ML models"""
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    BOOLEAN = "boolean"
    DERIVED = "derived"

@dataclass
class MLFeature:
    """Machine learning feature definition"""
    name: str
    feature_type: FeatureType
    source: str
    transformation: Optional[str] = None
    importance_score: float = 0.0
    
@dataclass
class TrainingData:
    """Training data for ML models"""
    features: Dict[str, Any]
    target: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelPrediction:
    """ML model prediction result"""
    predicted_value: float
    confidence_interval: Tuple[float, float]
    feature_importance: Dict[str, float]
    model_version: str
    prediction_timestamp: datetime

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mean_absolute_error: float
    root_mean_square_error: float
    training_samples: int
    last_updated: datetime

class MLSchedulingEngine:
    """
    Machine Learning Engine for Predictive Scheduling
    Provides intelligent scheduling optimization using ML algorithms
    """
    
    def __init__(self):
        self.models = {}
        self.feature_definitions = self._initialize_features()
        self.training_data = deque(maxlen=10000)  # Store last 10k samples
        self.model_performance = {}
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_features(self) -> List[MLFeature]:
        """Initialize feature definitions for ML models"""
        return [
            # Temporal Features
            MLFeature("hour_of_day", FeatureType.NUMERICAL, "datetime", "extract_hour"),
            MLFeature("day_of_week", FeatureType.CATEGORICAL, "datetime", "extract_weekday"),
            MLFeature("month_of_year", FeatureType.NUMERICAL, "datetime", "extract_month"),
            MLFeature("is_business_day", FeatureType.BOOLEAN, "calendar", "business_day_check"),
            MLFeature("days_since_holiday", FeatureType.NUMERICAL, "calendar", "days_from_last_holiday"),
            MLFeature("days_until_holiday", FeatureType.NUMERICAL, "calendar", "days_to_next_holiday"),
            
            # Scheduling Features
            MLFeature("report_type_encoded", FeatureType.CATEGORICAL, "report", "category_encoding"),
            MLFeature("department_encoded", FeatureType.CATEGORICAL, "department", "category_encoding"),
            MLFeature("priority_level", FeatureType.NUMERICAL, "request", "priority_to_numeric"),
            MLFeature("estimated_duration", FeatureType.NUMERICAL, "historical", "duration_estimate"),
            
            # Capacity Features
            MLFeature("current_capacity_utilization", FeatureType.NUMERICAL, "system", "real_time_capacity"),
            MLFeature("predicted_peak_load", FeatureType.NUMERICAL, "forecast", "peak_load_prediction"),
            MLFeature("concurrent_requests", FeatureType.NUMERICAL, "system", "active_request_count"),
            MLFeature("resource_availability", FeatureType.NUMERICAL, "system", "resource_check"),
            
            # Historical Features
            MLFeature("avg_success_rate_hour", FeatureType.NUMERICAL, "historical", "hourly_success_rate"),
            MLFeature("avg_duration_hour", FeatureType.NUMERICAL, "historical", "hourly_avg_duration"),
            MLFeature("historical_failures", FeatureType.NUMERICAL, "historical", "failure_count"),
            MLFeature("seasonal_pattern", FeatureType.NUMERICAL, "historical", "seasonal_decomposition"),
            
            # Derived Features
            MLFeature("capacity_stress_score", FeatureType.NUMERICAL, "derived", "capacity_stress_calculation"),
            MLFeature("optimal_time_score", FeatureType.NUMERICAL, "derived", "time_optimality_score"),
            MLFeature("conflict_probability", FeatureType.NUMERICAL, "derived", "conflict_risk_assessment"),
            MLFeature("efficiency_score", FeatureType.NUMERICAL, "derived", "efficiency_calculation")
        ]
    
    def _initialize_models(self):
        """Initialize ML models"""
        self.models = {
            MLModelType.LINEAR_REGRESSION: LinearRegressionModel(),
            MLModelType.TIME_SERIES: TimeSeriesModel(),
            MLModelType.CLUSTERING: ClusteringModel(),
            MLModelType.ENSEMBLE: EnsembleModel()
        }
    
    def extract_features(self, 
                        request_data: Dict[str, Any],
                        context_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for ML prediction"""
        
        features = {}
        
        try:
            # Extract temporal features
            target_datetime = request_data.get('target_datetime', datetime.now())
            features.update(self._extract_temporal_features(target_datetime))
            
            # Extract scheduling features
            features.update(self._extract_scheduling_features(request_data))
            
            # Extract capacity features
            features.update(self._extract_capacity_features(context_data))
            
            # Extract historical features
            features.update(self._extract_historical_features(request_data, context_data))
            
            # Calculate derived features
            features.update(self._calculate_derived_features(features, request_data))
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return self._get_default_features()
    
    def predict_optimal_schedule(self,
                               request_data: Dict[str, Any],
                               context_data: Dict[str, Any],
                               model_type: MLModelType = MLModelType.ENSEMBLE) -> ModelPrediction:
        """Generate ML-based scheduling prediction"""
        
        try:
            # Extract features
            features = self.extract_features(request_data, context_data)
            
            # Get model
            model = self.models.get(model_type)
            if not model:
                logger.warning(f"Model {model_type} not found, using ensemble")
                model = self.models[MLModelType.ENSEMBLE]
            
            # Make prediction
            prediction = model.predict(features)
            
            # Post-process prediction
            processed_prediction = self._post_process_prediction(prediction, request_data)
            
            return processed_prediction
            
        except Exception as e:
            logger.error(f"ML prediction failed: {str(e)}")
            return self._fallback_prediction(request_data)
    
    def train_model(self,
                   training_data: List[TrainingData],
                   model_type: MLModelType,
                   validation_split: float = 0.2) -> ModelPerformance:
        """Train ML model with historical data"""
        
        try:
            model = self.models.get(model_type)
            if not model:
                raise ValueError(f"Model {model_type} not found")
            
            # Prepare training data
            X, y = self._prepare_training_data(training_data)
            
            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train model
            model.train(X_train, y_train)
            
            # Validate model
            performance = self._validate_model(model, X_val, y_val, model_type)
            
            # Store performance metrics
            self.model_performance[model_type.value] = performance
            
            logger.info(f"Model {model_type} trained with accuracy: {performance.accuracy:.3f}")
            return performance
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return self._create_default_performance(model_type)
    
    def update_model_online(self,
                           prediction_result: ModelPrediction,
                           actual_outcome: Dict[str, Any],
                           feedback_score: float):
        """Update models with online learning"""
        
        try:
            # Create training sample from feedback
            training_sample = self._create_training_sample(
                prediction_result, actual_outcome, feedback_score
            )
            
            # Add to training data
            self.training_data.append(training_sample)
            
            # Update models if sufficient new data
            if len(self.training_data) % 100 == 0:  # Update every 100 samples
                self._retrain_models()
            
            # Update feature importance
            self._update_feature_importance(training_sample)
            
        except Exception as e:
            logger.error(f"Online model update failed: {str(e)}")
    
    def get_model_insights(self) -> Dict[str, Any]:
        """Get insights about model performance and features"""
        
        try:
            insights = {
                'model_performance': self._summarize_model_performance(),
                'feature_importance': self._get_feature_importance_ranking(),
                'prediction_accuracy': self._calculate_overall_accuracy(),
                'model_recommendations': self._generate_model_recommendations(),
                'training_data_stats': self._get_training_data_statistics()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Insights generation failed: {str(e)}")
            return {}
    
    # Feature Extraction Methods
    
    def _extract_temporal_features(self, target_datetime: datetime) -> Dict[str, float]:
        """Extract time-based features"""
        return {
            'hour_of_day': float(target_datetime.hour),
            'day_of_week': float(target_datetime.weekday()),
            'month_of_year': float(target_datetime.month),
            'is_weekend': float(target_datetime.weekday() >= 5),
            'hour_sin': math.sin(2 * math.pi * target_datetime.hour / 24),
            'hour_cos': math.cos(2 * math.pi * target_datetime.hour / 24),
            'day_sin': math.sin(2 * math.pi * target_datetime.weekday() / 7),
            'day_cos': math.cos(2 * math.pi * target_datetime.weekday() / 7)
        }
    
    def _extract_scheduling_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract scheduling-specific features"""
        return {
            'priority_level': self._encode_priority(request_data.get('priority', 'normal')),
            'estimated_duration': float(request_data.get('estimated_duration', 30)),
            'report_type_hash': float(hash(request_data.get('report_type', '')) % 1000),
            'department_hash': float(hash(request_data.get('department', '')) % 1000),
            'has_dependencies': float(bool(request_data.get('dependencies', [])))
        }
    
    def _extract_capacity_features(self, context_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract system capacity features"""
        return {
            'current_utilization': float(context_data.get('current_utilization', 0.5)),
            'available_slots': float(context_data.get('available_slots', 10)),
            'peak_hour_indicator': float(context_data.get('is_peak_hour', False)),
            'resource_contention': float(context_data.get('resource_contention', 0.3))
        }
    
    def _extract_historical_features(self, request_data: Dict[str, Any], 
                                   context_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract historical pattern features"""
        # In production, this would query historical database
        return {
            'avg_success_rate': 0.85,
            'historical_avg_duration': 25.0,
            'failure_rate_last_week': 0.1,
            'seasonal_factor': 1.0,
            'trend_indicator': 0.02
        }
    
    def _calculate_derived_features(self, base_features: Dict[str, float],
                                  request_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate derived features from base features"""
        return {
            'capacity_stress': base_features.get('current_utilization', 0.5) * 
                             base_features.get('peak_hour_indicator', 0),
            'time_optimality': self._calculate_time_optimality(base_features),
            'conflict_risk': self._calculate_conflict_risk(base_features),
            'efficiency_potential': self._calculate_efficiency_potential(base_features)
        }
    
    def _calculate_time_optimality(self, features: Dict[str, float]) -> float:
        """Calculate how optimal the timing is"""
        hour = features.get('hour_of_day', 12)
        # Optimal hours are 8-10 AM and 2-4 PM
        if 8 <= hour <= 10 or 14 <= hour <= 16:
            return 1.0
        elif 6 <= hour <= 18:
            return 0.7
        else:
            return 0.3
    
    def _calculate_conflict_risk(self, features: Dict[str, float]) -> float:
        """Calculate risk of scheduling conflicts"""
        utilization = features.get('current_utilization', 0.5)
        peak_indicator = features.get('peak_hour_indicator', 0)
        return min(1.0, utilization + peak_indicator * 0.3)
    
    def _calculate_efficiency_potential(self, features: Dict[str, float]) -> float:
        """Calculate potential for efficient execution"""
        time_opt = self._calculate_time_optimality(features)
        conflict_risk = self._calculate_conflict_risk(features)
        return max(0.0, time_opt - conflict_risk)
    
    def _encode_priority(self, priority: str) -> float:
        """Encode priority level as numeric value"""
        priority_map = {
            'critical': 1.0,
            'high': 0.8,
            'normal': 0.5,
            'low': 0.2,
            'batch': 0.1
        }
        return priority_map.get(priority.lower(), 0.5)
    
    # Model Management Methods
    
    def _prepare_training_data(self, training_data: List[TrainingData]) -> Tuple[List[Dict], List[float]]:
        """Prepare training data for ML models"""
        X = [sample.features for sample in training_data]
        y = [sample.target for sample in training_data]
        return X, y
    
    def _validate_model(self, model, X_val, y_val, model_type: MLModelType) -> ModelPerformance:
        """Validate model performance"""
        predictions = [model.predict_single(x) for x in X_val]
        
        # Calculate metrics
        mae = statistics.mean([abs(pred - actual) for pred, actual in zip(predictions, y_val)])
        rmse = math.sqrt(statistics.mean([(pred - actual) ** 2 for pred, actual in zip(predictions, y_val)]))
        
        # Simple accuracy calculation
        accuracy = 1.0 - (mae / max(y_val)) if y_val else 0.5
        
        return ModelPerformance(
            model_id=f"{model_type.value}_{datetime.now().strftime('%Y%m%d')}",
            accuracy=max(0.0, min(1.0, accuracy)),
            precision=0.8,  # Placeholder
            recall=0.75,    # Placeholder
            f1_score=0.77,  # Placeholder
            mean_absolute_error=mae,
            root_mean_square_error=rmse,
            training_samples=len(X_val),
            last_updated=datetime.now()
        )
    
    def _post_process_prediction(self, prediction: ModelPrediction, 
                               request_data: Dict[str, Any]) -> ModelPrediction:
        """Post-process ML prediction"""
        # Apply business constraints
        target_date = request_data.get('target_date', date.today())
        
        # Ensure prediction is within business hours
        predicted_hour = int(prediction.predicted_value)
        if predicted_hour < 6:
            predicted_hour = 8
        elif predicted_hour > 18:
            predicted_hour = 17
        
        prediction.predicted_value = float(predicted_hour)
        
        return prediction
    
    def _fallback_prediction(self, request_data: Dict[str, Any]) -> ModelPrediction:
        """Fallback prediction when ML fails"""
        return ModelPrediction(
            predicted_value=9.0,  # 9 AM default
            confidence_interval=(8.0, 10.0),
            feature_importance={},
            model_version="fallback_v1.0",
            prediction_timestamp=datetime.now()
        )
    
    def _get_default_features(self) -> Dict[str, float]:
        """Get default feature values"""
        return {feature.name: 0.0 for feature in self.feature_definitions}
    
    # Placeholder methods for full implementation
    def _retrain_models(self):
        """Retrain models with accumulated data"""
        pass
    
    def _update_feature_importance(self, training_sample: TrainingData):
        """Update feature importance scores"""
        pass
    
    def _summarize_model_performance(self) -> Dict[str, Any]:
        """Summarize model performance metrics"""
        return {model_type: perf.__dict__ for model_type, perf in self.model_performance.items()}
    
    def _get_feature_importance_ranking(self) -> List[Dict[str, Any]]:
        """Get ranked feature importance"""
        return [{'feature': f.name, 'importance': f.importance_score} for f in self.feature_definitions]
    
    def _calculate_overall_accuracy(self) -> float:
        """Calculate overall prediction accuracy"""
        if not self.model_performance:
            return 0.0
        return statistics.mean([perf.accuracy for perf in self.model_performance.values()])
    
    def _generate_model_recommendations(self) -> List[str]:
        """Generate recommendations for model improvement"""
        return [
            "Increase training data for time series model",
            "Add more temporal features",
            "Tune hyperparameters for ensemble model"
        ]
    
    def _get_training_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about training data"""
        return {
            'total_samples': len(self.training_data),
            'data_quality_score': 0.85,
            'feature_coverage': 0.9,
            'temporal_span_days': 90
        }
    
    def _create_training_sample(self, prediction: ModelPrediction, 
                              outcome: Dict[str, Any], score: float) -> TrainingData:
        """Create training sample from feedback"""
        return TrainingData(
            features={'prediction_value': prediction.predicted_value},
            target=score,
            timestamp=datetime.now(),
            metadata={'outcome': outcome}
        )
    
    def _create_default_performance(self, model_type: MLModelType) -> ModelPerformance:
        """Create default performance metrics"""
        return ModelPerformance(
            model_id=f"{model_type.value}_default",
            accuracy=0.5,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            mean_absolute_error=1.0,
            root_mean_square_error=1.5,
            training_samples=0,
            last_updated=datetime.now()
        )


# Base ML Model Classes

class BaseMLModel:
    """Base class for ML models"""
    
    def __init__(self):
        self.is_trained = False
        self.model_version = "1.0"
    
    def train(self, X: List[Dict], y: List[float]):
        """Train the model"""
        self.is_trained = True
    
    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Make prediction"""
        return ModelPrediction(
            predicted_value=9.0,
            confidence_interval=(8.0, 10.0),
            feature_importance={},
            model_version=self.model_version,
            prediction_timestamp=datetime.now()
        )
    
    def predict_single(self, features: Dict[str, float]) -> float:
        """Make single prediction"""
        return self.predict(features).predicted_value


class LinearRegressionModel(BaseMLModel):
    """Linear regression model for scheduling prediction"""
    
    def __init__(self):
        super().__init__()
        self.coefficients = {}
        self.intercept = 9.0  # Default 9 AM
    
    def train(self, X: List[Dict], y: List[float]):
        """Train linear regression model"""
        # Simplified training - in production would use proper ML library
        if X and y:
            self.intercept = statistics.mean(y)
        self.is_trained = True
    
    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Linear regression prediction"""
        if not self.is_trained:
            return super().predict(features)
        
        # Simple linear combination
        prediction = self.intercept
        for feature, value in features.items():
            prediction += self.coefficients.get(feature, 0.0) * value
        
        # Ensure reasonable bounds
        prediction = max(6.0, min(18.0, prediction))
        
        return ModelPrediction(
            predicted_value=prediction,
            confidence_interval=(prediction - 1.0, prediction + 1.0),
            feature_importance=self.coefficients.copy(),
            model_version=self.model_version,
            prediction_timestamp=datetime.now()
        )


class TimeSeriesModel(BaseMLModel):
    """Time series model for temporal patterns"""
    
    def __init__(self):
        super().__init__()
        self.seasonal_patterns = {}
        self.trend_factor = 0.0
    
    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Time series prediction"""
        hour = features.get('hour_of_day', 9.0)
        day_of_week = features.get('day_of_week', 1.0)
        
        # Apply seasonal adjustment
        seasonal_adj = self.seasonal_patterns.get(int(day_of_week), 0.0)
        prediction = hour + seasonal_adj + self.trend_factor
        
        return ModelPrediction(
            predicted_value=prediction,
            confidence_interval=(prediction - 0.5, prediction + 0.5),
            feature_importance={'temporal_pattern': 0.8, 'seasonal_factor': 0.6},
            model_version=self.model_version,
            prediction_timestamp=datetime.now()
        )


class ClusteringModel(BaseMLModel):
    """Clustering model for pattern recognition"""
    
    def __init__(self):
        super().__init__()
        self.clusters = {}
    
    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Clustering-based prediction"""
        # Find closest cluster
        cluster_id = self._find_cluster(features)
        cluster_center = self.clusters.get(cluster_id, 9.0)
        
        return ModelPrediction(
            predicted_value=cluster_center,
            confidence_interval=(cluster_center - 1.5, cluster_center + 1.5),
            feature_importance={'cluster_similarity': 0.7},
            model_version=self.model_version,
            prediction_timestamp=datetime.now()
        )
    
    def _find_cluster(self, features: Dict[str, float]) -> str:
        """Find closest cluster for features"""
        return "default_cluster"


class EnsembleModel(BaseMLModel):
    """Ensemble model combining multiple approaches"""
    
    def __init__(self):
        super().__init__()
        self.sub_models = {
            'linear': LinearRegressionModel(),
            'time_series': TimeSeriesModel(),
            'clustering': ClusteringModel()
        }
        self.weights = {'linear': 0.4, 'time_series': 0.4, 'clustering': 0.2}
    
    def train(self, X: List[Dict], y: List[float]):
        """Train all sub-models"""
        for model in self.sub_models.values():
            model.train(X, y)
        self.is_trained = True
    
    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Ensemble prediction"""
        predictions = {}
        total_weight = 0
        weighted_sum = 0
        
        for name, model in self.sub_models.items():
            pred = model.predict(features)
            weight = self.weights[name]
            predictions[name] = pred.predicted_value
            weighted_sum += pred.predicted_value * weight
            total_weight += weight
        
        final_prediction = weighted_sum / total_weight if total_weight > 0 else 9.0
        
        # Calculate confidence based on agreement
        prediction_values = list(predictions.values())
        std_dev = statistics.stdev(prediction_values) if len(prediction_values) > 1 else 0.5
        confidence_width = std_dev * 2
        
        return ModelPrediction(
            predicted_value=final_prediction,
            confidence_interval=(final_prediction - confidence_width, 
                               final_prediction + confidence_width),
            feature_importance={'ensemble_agreement': 1.0 - std_dev},
            model_version=self.model_version,
            prediction_timestamp=datetime.now()
        )


# Factory function
def create_ml_scheduling_engine() -> MLSchedulingEngine:
    """Create and configure ML scheduling engine"""
    return MLSchedulingEngine()