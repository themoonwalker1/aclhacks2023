from django.db import models
from qiskit import QuantumCircuit
import numpy as np
import secrets

class QuantumModel(models.Model):
    key = models.CharField(max_length=32, unique=True)
    alice = models.CharField(max_length=2**16, null=True)
    bob = models.CharField(max_length=2**16, null=True)
    alice_key = models.JSONField(null=True)
    alice_table = models.JSONField(null=True)
    message = models.CharField(max_length=2**16, null=True)

    def save(self, *args, **kwargs):
        # Generate a secure and random hex key
        self.key = secrets.token_hex(16)
        super().save(*args, **kwargs)

    def set_alice_key(self, alice_key):
        self.alice_key = alice_key

    def get_alice_key(self):
        return self.alice_key

    def set_alice_circuit(self, alice_circuit):
        self.alice = alice_circuit.qasm()

    def get_alice_circuit(self):
        return QuantumCircuit.from_qasm_str(self.alice)

    def set_bob_circuit(self, bob_circuit):
        self.bob = bob_circuit.qasm()

    def get_bob_circuit(self):
        return QuantumCircuit.from_qasm_str(self.bob)

    def __str__(self):
        return str(self.alice_table) + " " + str(self.alice_key)
