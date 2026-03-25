"""
NetworkAutoencoder: Keras encoder-decoder for anomaly detection
Reconstruction loss serves as anomaly score
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from typing import Tuple

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class NetworkAutoencoder(Model):
    """
    Autoencoder for network flow anomaly detection.
    Encodes flows to latent representation, reconstructs, uses MSE as anomaly score.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: list = None,
        latent_dim: int = 16,
        dropout_rate: float = 0.2,
        **kwargs
    ):
        """
        Initialize autoencoder architecture.

        Args:
            input_dim: Input feature dimension
            hidden_dims: List of hidden layer dimensions (e.g., [128, 64, 32])
            latent_dim: Latent representation dimension
            dropout_rate: Dropout probability
        """
        super(NetworkAutoencoder, self).__init__(**kwargs)

        if hidden_dims is None:
            hidden_dims = [128, 64, 32]

        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims

        logger.info(
            f"Initializing NetworkAutoencoder: input={input_dim}, hidden={hidden_dims}, latent={latent_dim}"
        )

        # Build encoder
        encoder_inputs = keras.Input(shape=(input_dim,))
        x = encoder_inputs
        
        for hidden_dim in hidden_dims:
            x = layers.Dense(hidden_dim, activation='relu')(x)
            if dropout_rate > 0:
                x = layers.Dropout(dropout_rate)(x)
        
        # Bottleneck (latent layer)
        latent_output = layers.Dense(latent_dim, activation='relu', name='latent')(x)
        self.encoder = Model(encoder_inputs, latent_output, name='encoder')

        # Build decoder
        decoder_inputs = keras.Input(shape=(latent_dim,))
        x = decoder_inputs
        
        decoder_hidden_dims = list(reversed(hidden_dims))
        for hidden_dim in decoder_hidden_dims:
            x = layers.Dense(hidden_dim, activation='relu')(x)
            if dropout_rate > 0:
                x = layers.Dropout(dropout_rate)(x)
        
        # Output layer (reconstruct to original dimension)
        decoder_output = layers.Dense(input_dim, activation='linear')(x)
        self.decoder = Model(decoder_inputs, decoder_output, name='decoder')

        logger.info("NetworkAutoencoder initialized successfully")

    def call(self, x, training=False):
        """
        Forward pass: encode → decode.

        Args:
            x: Input [batch_size, input_dim]
            training: Whether in training mode

        Returns:
            Tuple of (reconstructed_output, latent_representation)
        """
        z = self.encoder(x, training=training)
        reconstructed = self.decoder(z, training=training)
        return reconstructed, z

    def reconstruction_loss(self, x, reconstructed):
        """
        Compute reconstruction loss (MSE).

        Args:
            x: Original input [batch_size, input_dim]
            reconstructed: Reconstructed output [batch_size, input_dim]

        Returns:
            MSE loss (scalar tensor)
        """
        return tf.reduce_mean(tf.square(x - reconstructed))

    def anomaly_score(self, x):
        """
        Compute anomaly score for input (per-sample reconstruction loss).

        Args:
            x: Input [batch_size, input_dim]

        Returns:
            Anomaly scores [batch_size] - MSE per sample
        """
        reconstructed, _ = self(x, training=False)
        # Per-sample MSE
        scores = tf.reduce_mean(tf.square(x - reconstructed), axis=1)
        return scores.numpy()
