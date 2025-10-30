# Predictive Scheduling Analytics Tests - Phase B Sprint 2 Day 6 Option B
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.analytics.predictive_scheduling_service import (
    PredictiveSchedulingService,
    PredictionModel,
    SchedulingPriority,
    OptimizationGoal,
    DeliveryPattern,
    HolidayType,
    PredictionResult,
    create_predictive_scheduling_service
)
from app.services.analytics.ml_scheduling_engine import (
    MLSchedulingEngine,
    MLModelType,
    TrainingData,
    ModelPrediction,
    create_ml_scheduling_engine
)

class TestPredictiveSchedulingService:
    """Test suite for Predictive Scheduling Service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def predictive_service(self, mock_db):
        """Create predictive scheduling service with mocked dependencies"""
        service = PredictiveSchedulingService(mock_db)
        
        # Mock database queries
        mock_db.execute.return_value.scalar.return_value = False
        mock_db.execute.return_value.fetchall.return_value = []
        
        return service
    
    def test_service_initialization(self, predictive_service):
        """Test service initialization"""
        assert predictive_service.db is not None
        assert hasattr(predictive_service, 'delivery_patterns')
        assert hasattr(predictive_service, 'capacity_baselines')
        assert hasattr(predictive_service, 'models')
        assert len(predictive_service.models) == 6  # All prediction models
    
    def test_predict_optimal_delivery_time_hybrid(self, predictive_service):
        """Test hybrid model prediction"""
        prediction = predictive_service.predict_optimal_delivery_time(
            report_type="Quality Report",
            department="Quality",
            target_date=date(2024, 1, 15),
            priority=SchedulingPriority.NORMAL,
            model=PredictionModel.HYBRID
        )
        
        assert isinstance(prediction, PredictionResult)
        assert prediction.recommended_time is not None
        assert 0.0 <= prediction.confidence_score <= 1.0
        assert prediction.model_used == PredictionModel.HYBRID
        assert len(prediction.optimization_factors) > 0
    
    def test_predict_optimal_delivery_time_historical(self, predictive_service):
        """Test historical pattern prediction"""
        prediction = predictive_service.predict_optimal_delivery_time(
            report_type="Quality Report",
            department="Quality",
            target_date=date(2024, 1, 15),
            priority=SchedulingPriority.HIGH,
            model=PredictionModel.HISTORICAL_PATTERN
        )
        
        assert isinstance(prediction, PredictionResult)
        assert prediction.model_used == PredictionModel.HISTORICAL_PATTERN
        assert prediction.confidence_score > 0
    
    def test_predict_critical_priority(self, predictive_service):
        """Test prediction with critical priority"""
        prediction = predictive_service.predict_optimal_delivery_time(
            report_type="Critical Report",
            department="Safety",
            target_date=date(2024, 1, 15),
            priority=SchedulingPriority.CRITICAL
        )
        
        assert prediction.recommended_time.hour <= 10  # Critical gets early slots
        assert prediction.confidence_score >= 0.0
    
    def test_analyze_delivery_patterns(self, predictive_service):
        """Test delivery pattern analysis"""
        analysis = predictive_service.analyze_delivery_patterns(days_back=30)
        
        assert 'analysis_period' in analysis
        assert 'patterns' in analysis
        assert 'metrics' in analysis
        assert 'insights' in analysis
        
        # Check metrics structure
        metrics = analysis['metrics']
        assert 'total_deliveries' in metrics
        assert 'success_rate' in metrics
        assert 'peak_hours' in metrics
        assert 'seasonal_trends' in metrics
    
    def test_forecast_capacity_demand(self, predictive_service):
        """Test capacity demand forecasting"""
        forecast = predictive_service.forecast_capacity_demand(forecast_days=14)
        
        assert 'forecast_period' in forecast
        assert 'summary' in forecast
        assert 'daily_forecasts' in forecast
        assert 'recommendations' in forecast
        assert 'confidence_metrics' in forecast
        
        # Validate forecast structure
        summary = forecast['summary']
        assert 'total_predicted_deliveries' in summary
        assert 'average_daily_demand' in summary
        assert 'peak_demand_days' in summary
    
    def test_optimize_schedule(self, predictive_service):
        """Test schedule optimization"""
        optimization = predictive_service.optimize_schedule(
            target_date=date(2024, 1, 15),
            goal=OptimizationGoal.BALANCE_LOAD
        )
        
        assert optimization.target_date == date(2024, 1, 15)
        assert optimization.recommendation_id is not None
        assert 'current_schedule' in optimization.__dict__
        assert 'optimized_schedule' in optimization.__dict__
        assert 'improvement_metrics' in optimization.__dict__
        assert len(optimization.expected_benefits) >= 0
    
    def test_get_scheduling_insights(self, predictive_service):
        """Test insights generation"""
        insights = predictive_service.get_scheduling_insights(
            department="Quality",
            days_back=30
        )
        
        assert 'analysis_period' in insights
        assert 'insights' in insights
        
        insights_data = insights['insights']
        assert 'executive_summary' in insights_data
        assert 'key_findings' in insights_data
        assert 'recommendations' in insights_data
        assert 'performance_metrics' in insights_data
    
    def test_learn_from_feedback(self, predictive_service):
        """Test learning from feedback"""
        result = predictive_service.learn_from_feedback(
            prediction_id="test_pred_001",
            actual_outcome={"delivered_at": "2024-01-15T09:30:00", "success": True},
            feedback_score=0.85
        )
        
        assert result == True
    
    def test_factory_function(self, mock_db):
        """Test factory function"""
        service = create_predictive_scheduling_service(mock_db)
        
        assert isinstance(service, PredictiveSchedulingService)
        assert service.db == mock_db


class TestMLSchedulingEngine:
    """Test suite for ML Scheduling Engine"""
    
    @pytest.fixture
    def ml_engine(self):
        """Create ML scheduling engine"""
        return MLSchedulingEngine()
    
    def test_engine_initialization(self, ml_engine):
        """Test ML engine initialization"""
        assert len(ml_engine.models) > 0
        assert len(ml_engine.feature_definitions) > 0
        assert ml_engine.training_data is not None
    
    def test_extract_features(self, ml_engine):
        """Test feature extraction"""
        request_data = {
            'target_datetime': datetime(2024, 1, 15, 9, 0),
            'report_type': 'Quality Report',
            'department': 'Quality',
            'priority': 'high',
            'estimated_duration': 30
        }
        
        context_data = {
            'current_utilization': 0.6,
            'available_slots': 8,
            'is_peak_hour': False,
            'resource_contention': 0.3
        }
        
        features = ml_engine.extract_features(request_data, context_data)
        
        assert isinstance(features, dict)
        assert len(features) > 0
        assert 'hour_of_day' in features
        assert 'day_of_week' in features
        assert 'priority_level' in features
        assert 'current_utilization' in features
    
    def test_predict_optimal_schedule(self, ml_engine):
        """Test ML prediction"""
        request_data = {
            'target_datetime': datetime(2024, 1, 15, 9, 0),
            'report_type': 'Quality Report',
            'department': 'Quality'
        }
        
        context_data = {
            'current_utilization': 0.5,
            'available_slots': 10
        }
        
        prediction = ml_engine.predict_optimal_schedule(
            request_data=request_data,
            context_data=context_data,
            model_type=MLModelType.ENSEMBLE
        )
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.predicted_value >= 0
        assert len(prediction.confidence_interval) == 2
        assert prediction.model_version is not None
    
    def test_train_model(self, ml_engine):
        """Test model training"""
        # Create sample training data
        training_data = [
            TrainingData(
                features={'hour_of_day': 9, 'priority_level': 0.8},
                target=9.5,
                timestamp=datetime.now()
            ),
            TrainingData(
                features={'hour_of_day': 14, 'priority_level': 0.5},
                target=14.2,
                timestamp=datetime.now()
            )
        ]
        
        performance = ml_engine.train_model(
            training_data=training_data,
            model_type=MLModelType.LINEAR_REGRESSION,
            validation_split=0.2
        )
        
        assert performance.model_id is not None
        assert 0.0 <= performance.accuracy <= 1.0
        assert performance.training_samples >= 0
    
    def test_update_model_online(self, ml_engine):
        """Test online model updates"""
        prediction = ModelPrediction(
            predicted_value=9.0,
            confidence_interval=(8.0, 10.0),
            feature_importance={},
            model_version="test_v1",
            prediction_timestamp=datetime.now()
        )
        
        actual_outcome = {
            'delivered_at': datetime(2024, 1, 15, 9, 30),
            'success': True,
            'duration': 25
        }
        
        # Should not raise exception
        ml_engine.update_model_online(prediction, actual_outcome, 0.85)
    
    def test_get_model_insights(self, ml_engine):
        """Test model insights generation"""
        insights = ml_engine.get_model_insights()
        
        assert isinstance(insights, dict)
        # Basic structure validation
        if insights:  # May be empty in test environment
            assert 'model_performance' in insights or len(insights) == 0
    
    def test_temporal_feature_extraction(self, ml_engine):
        """Test temporal feature extraction"""
        target_datetime = datetime(2024, 1, 15, 14, 30)  # Monday 2:30 PM
        
        features = ml_engine._extract_temporal_features(target_datetime)
        
        assert features['hour_of_day'] == 14.0
        assert features['day_of_week'] == 0.0  # Monday
        assert features['month_of_year'] == 1.0
        assert features['is_weekend'] == 0.0  # Monday is not weekend
        assert 'hour_sin' in features
        assert 'hour_cos' in features
    
    def test_scheduling_feature_extraction(self, ml_engine):
        """Test scheduling feature extraction"""
        request_data = {
            'priority': 'high',
            'estimated_duration': 45,
            'report_type': 'Quality Report',
            'department': 'Quality',
            'dependencies': ['report_a', 'report_b']
        }
        
        features = ml_engine._extract_scheduling_features(request_data)
        
        assert features['priority_level'] == 0.8  # High priority
        assert features['estimated_duration'] == 45.0
        assert features['has_dependencies'] == 1.0  # Has dependencies
        assert 'report_type_hash' in features
        assert 'department_hash' in features
    
    def test_capacity_feature_extraction(self, ml_engine):
        """Test capacity feature extraction"""
        context_data = {
            'current_utilization': 0.75,
            'available_slots': 5,
            'is_peak_hour': True,
            'resource_contention': 0.4
        }
        
        features = ml_engine._extract_capacity_features(context_data)
        
        assert features['current_utilization'] == 0.75
        assert features['available_slots'] == 5.0
        assert features['peak_hour_indicator'] == 1.0
        assert features['resource_contention'] == 0.4
    
    def test_derived_feature_calculation(self, ml_engine):
        """Test derived feature calculations"""
        base_features = {
            'hour_of_day': 9.0,
            'current_utilization': 0.6,
            'peak_hour_indicator': 0.0
        }
        
        derived = ml_engine._calculate_derived_features(base_features, {})
        
        assert 'capacity_stress' in derived
        assert 'time_optimality' in derived
        assert 'conflict_risk' in derived
        assert 'efficiency_potential' in derived
        
        # Capacity stress should be utilization * peak indicator
        assert derived['capacity_stress'] == 0.6 * 0.0
    
    def test_time_optimality_calculation(self, ml_engine):
        """Test time optimality scoring"""
        # Test optimal hours (8-10 AM)
        features_optimal = {'hour_of_day': 9.0}
        optimality = ml_engine._calculate_time_optimality(features_optimal)
        assert optimality == 1.0
        
        # Test good hours (6-18)
        features_good = {'hour_of_day': 12.0}
        optimality = ml_engine._calculate_time_optimality(features_good)
        assert optimality == 0.7
        
        # Test poor hours (outside business)
        features_poor = {'hour_of_day': 22.0}
        optimality = ml_engine._calculate_time_optimality(features_poor)
        assert optimality == 0.3
    
    def test_factory_function_ml(self):
        """Test ML engine factory function"""
        engine = create_ml_scheduling_engine()
        
        assert isinstance(engine, MLSchedulingEngine)
        assert len(engine.models) > 0


class TestMLModels:
    """Test suite for individual ML models"""
    
    def test_base_ml_model(self):
        """Test base ML model"""
        from app.services.analytics.ml_scheduling_engine import BaseMLModel
        
        model = BaseMLModel()
        assert not model.is_trained
        
        # Test training
        model.train([], [])
        assert model.is_trained
        
        # Test prediction
        prediction = model.predict({})
        assert isinstance(prediction, ModelPrediction)
        assert prediction.predicted_value == 9.0  # Default
    
    def test_linear_regression_model(self):
        """Test linear regression model"""
        from app.services.analytics.ml_scheduling_engine import LinearRegressionModel
        
        model = LinearRegressionModel()
        
        # Test training
        X = [{'feature1': 1.0}, {'feature1': 2.0}]
        y = [9.0, 10.0]
        model.train(X, y)
        assert model.is_trained
        assert model.intercept == 9.5  # Mean of y values
        
        # Test prediction
        features = {'feature1': 1.5}
        prediction = model.predict(features)
        assert isinstance(prediction, ModelPrediction)
        assert 6.0 <= prediction.predicted_value <= 18.0  # Within bounds
    
    def test_time_series_model(self):
        """Test time series model"""
        from app.services.analytics.ml_scheduling_engine import TimeSeriesModel
        
        model = TimeSeriesModel()
        
        features = {'hour_of_day': 9.0, 'day_of_week': 1.0}
        prediction = model.predict(features)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.feature_importance['temporal_pattern'] == 0.8
    
    def test_clustering_model(self):
        """Test clustering model"""
        from app.services.analytics.ml_scheduling_engine import ClusteringModel
        
        model = ClusteringModel()
        
        features = {'hour_of_day': 9.0, 'department_hash': 123.0}
        prediction = model.predict(features)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.feature_importance['cluster_similarity'] == 0.7
    
    def test_ensemble_model(self):
        """Test ensemble model"""
        from app.services.analytics.ml_scheduling_engine import EnsembleModel
        
        model = EnsembleModel()
        
        # Test training
        X = [{'feature1': 1.0}]
        y = [9.0]
        model.train(X, y)
        assert model.is_trained
        
        # Test prediction
        features = {'hour_of_day': 9.0, 'day_of_week': 1.0}
        prediction = model.predict(features)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.feature_importance['ensemble_agreement'] is not None


class TestPredictiveSchedulingIntegration:
    """Integration tests for the complete predictive scheduling system"""
    
    @pytest.mark.integration
    def test_end_to_end_prediction(self):
        """Test complete prediction workflow"""
        from unittest.mock import Mock
        from sqlalchemy.orm import Session
        
        # Mock database
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = False
        mock_db.execute.return_value.fetchall.return_value = []
        
        # Create services
        predictive_service = create_predictive_scheduling_service(mock_db)
        ml_engine = create_ml_scheduling_engine()
        
        # Test complete workflow
        prediction = predictive_service.predict_optimal_delivery_time(
            report_type="Integration Test Report",
            department="Testing",
            target_date=date.today() + timedelta(days=1),
            priority=SchedulingPriority.NORMAL,
            model=PredictionModel.HYBRID
        )
        
        assert prediction is not None
        assert prediction.confidence_score > 0
        assert prediction.recommended_time is not None
        
        # Test ML component
        request_data = {
            'target_datetime': prediction.recommended_time,
            'report_type': "Integration Test Report",
            'department': "Testing"
        }
        
        ml_prediction = ml_engine.predict_optimal_schedule(
            request_data=request_data,
            context_data={'current_utilization': 0.5}
        )
        
        assert ml_prediction is not None
        assert ml_prediction.predicted_value > 0
    
    @pytest.mark.integration
    def test_feedback_loop_integration(self):
        """Test feedback and learning integration"""
        from unittest.mock import Mock
        from sqlalchemy.orm import Session
        
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = False
        mock_db.execute.return_value.fetchall.return_value = []
        
        # Create services
        predictive_service = create_predictive_scheduling_service(mock_db)
        ml_engine = create_ml_scheduling_engine()
        
        # Generate prediction
        prediction = predictive_service.predict_optimal_delivery_time(
            report_type="Feedback Test Report",
            department="Testing",
            target_date=date.today() + timedelta(days=1)
        )
        
        # Simulate feedback
        actual_outcome = {
            'delivered_at': prediction.recommended_time + timedelta(minutes=15),
            'success': True,
            'duration': 25
        }
        
        # Provide feedback
        feedback_result = predictive_service.learn_from_feedback(
            prediction_id="test_feedback_001",
            actual_outcome=actual_outcome,
            feedback_score=0.9
        )
        
        assert feedback_result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])