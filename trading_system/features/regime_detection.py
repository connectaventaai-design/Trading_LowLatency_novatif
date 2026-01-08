"""Hidden Markov Model regime detection."""
import numpy as np
from typing import List, Dict, Any, Optional
from hmmlearn import hmm
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path


class RegimeDetector:
    """HMM-based market regime detector."""
    
    def __init__(
        self,
        n_states: int = 4,
        n_iter: int = 100,
        covariance_type: str = "full"
    ):
        """
        Initialize regime detector.
        
        Args:
            n_states: Number of hidden states (regimes)
            n_iter: Number of EM iterations
            covariance_type: Type of covariance matrix
        """
        self.n_states = n_states
        self.n_iter = n_iter
        self.model = hmm.GaussianHMM(
            n_components=n_states,
            covariance_type=covariance_type,
            n_iter=n_iter,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Regime labels
        self.regime_names = {
            0: "trending",
            1: "ranging",
            2: "high_volatility",
            3: "consolidation"
        }
        
    def prepare_features(self, data: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Prepare features for HMM.
        
        Args:
            data: Dictionary with price and volume data
            
        Returns:
            Feature matrix
        """
        features = []
        
        # Returns
        if 'close' in data:
            returns = np.diff(data['close']) / data['close'][:-1]
            features.append(returns)
            
        # Volatility (rolling std of returns)
        if len(features) > 0:
            window = 20
            volatility = np.array([
                np.std(returns[max(0, i-window):i+1])
                for i in range(len(returns))
            ])
            features.append(volatility)
            
        # Volume ratio
        if 'volume' in data and len(data['volume']) > 1:
            volume = data['volume'][1:]  # Match returns length
            volume_ma = np.array([
                np.mean(volume[max(0, i-20):i+1])
                for i in range(len(volume))
            ])
            volume_ratio = volume / (volume_ma + 1e-8)
            features.append(volume_ratio)
            
        # Trend strength (difference from MA)
        if 'close' in data:
            close = data['close'][1:]
            ma = np.array([
                np.mean(close[max(0, i-20):i+1])
                for i in range(len(close))
            ])
            trend_strength = (close - ma) / (ma + 1e-8)
            features.append(trend_strength)
            
        # Stack features
        feature_matrix = np.column_stack(features)
        return feature_matrix
        
    def fit(self, data: Dict[str, np.ndarray]) -> None:
        """
        Fit HMM to historical data.
        
        Args:
            data: Dictionary with price and volume data
        """
        features = self.prepare_features(data)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit HMM
        self.model.fit(features_scaled)
        self.is_fitted = True
        
    def predict_regime(self, data: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Predict regime for data.
        
        Args:
            data: Dictionary with price and volume data
            
        Returns:
            Array of regime states
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
            
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)
        
        # Predict states
        states = self.model.predict(features_scaled)
        return states
        
    def get_current_regime(self, data: Dict[str, np.ndarray]) -> str:
        """
        Get current market regime.
        
        Args:
            data: Dictionary with recent price and volume data
            
        Returns:
            Regime name
        """
        states = self.predict_regime(data)
        current_state = states[-1]
        return self.regime_names.get(current_state, "unknown")
        
    def get_regime_probabilities(self, data: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Get regime probabilities.
        
        Args:
            data: Dictionary with price and volume data
            
        Returns:
            Probability matrix (n_samples x n_states)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
            
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)
        
        # Get posterior probabilities
        posteriors = self.model.predict_proba(features_scaled)
        return posteriors
        
    def get_transition_matrix(self) -> np.ndarray:
        """Get regime transition probability matrix."""
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        return self.model.transmat_
        
    def classify_regime_characteristics(self, state: int) -> Dict[str, Any]:
        """
        Get characteristics of a regime state.
        
        Args:
            state: Regime state index
            
        Returns:
            Dictionary with regime characteristics
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
            
        means = self.model.means_[state]
        
        # Analyze means to classify regime
        # Feature order: [returns, volatility, volume_ratio, trend_strength]
        return {
            'state': state,
            'name': self.regime_names.get(state, "unknown"),
            'avg_return': means[0] if len(means) > 0 else 0,
            'volatility': means[1] if len(means) > 1 else 0,
            'volume_activity': means[2] if len(means) > 2 else 0,
            'trend_strength': means[3] if len(means) > 3 else 0,
        }
        
    def save_model(self, path: Path) -> None:
        """Save trained model."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_fitted': self.is_fitted,
                'regime_names': self.regime_names,
            }, f)
            
    def load_model(self, path: Path) -> None:
        """Load trained model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            self.regime_names = data['regime_names']


class AdaptiveParameterAdjuster:
    """Adjust strategy parameters based on detected regime."""
    
    def __init__(self, base_params: Dict[str, Any]):
        """
        Initialize parameter adjuster.
        
        Args:
            base_params: Base strategy parameters
        """
        self.base_params = base_params
        
        # Regime-specific adjustments
        self.regime_adjustments = {
            "trending": {
                'position_size_multiplier': 1.2,
                'stop_loss_multiplier': 1.5,
                'take_profit_multiplier': 2.0,
                'entry_threshold': 0.6,
            },
            "ranging": {
                'position_size_multiplier': 0.8,
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.5,
                'entry_threshold': 0.75,
            },
            "high_volatility": {
                'position_size_multiplier': 0.5,
                'stop_loss_multiplier': 2.0,
                'take_profit_multiplier': 2.5,
                'entry_threshold': 0.8,
            },
            "consolidation": {
                'position_size_multiplier': 0.6,
                'stop_loss_multiplier': 0.8,
                'take_profit_multiplier': 1.2,
                'entry_threshold': 0.7,
            },
        }
        
    def get_adjusted_params(self, regime: str) -> Dict[str, Any]:
        """
        Get adjusted parameters for current regime.
        
        Args:
            regime: Current regime name
            
        Returns:
            Adjusted parameters
        """
        adjusted = self.base_params.copy()
        
        if regime in self.regime_adjustments:
            adjustments = self.regime_adjustments[regime]
            
            # Apply multipliers
            for key, value in adjustments.items():
                if key in adjusted:
                    if 'multiplier' in key:
                        # Apply as multiplier
                        base_key = key.replace('_multiplier', '')
                        if base_key in adjusted:
                            adjusted[base_key] *= value
                    else:
                        # Direct replacement
                        adjusted[key] = value
                        
        return adjusted
