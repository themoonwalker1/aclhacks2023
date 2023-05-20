from django.db import models
import secrets

from qiskit import QuantumCircuit


class QuantumModel(models.Model):
    key = models.CharField(max_length=32, unique=True)
    alice = None  # Reference to the quantum computing model
    bob = None

    def save(self, *args, **kwargs):
        # Generate a secure and random hex key
        self.key = secrets.token_hex(16)
        super().save(*args, **kwargs)
