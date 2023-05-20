# Import necessary libraries and modules
from django.http import JsonResponse
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute, BasicAer
from qiskit.tools.visualization import plot_histogram
import numpy as np
from models import QuantumModel

# Quantum circuit for Alice state
qr = QuantumRegister(16, name='qr')
cr = ClassicalRegister(16, name='cr')

def SendState(qc1, qc2):
    ''' This function takes the output of a circuit qc1 (made up only of x and
        h gates and initializes another circuit qc2 with the same state
    '''

    qs = qc1.qasm().split(sep=';')[4:-1]

    for index, instruction in enumerate(qs):
        qs[index] = instruction.lstrip()

    for instruction in qs:
        if instruction[0] == 'x':
            old_qr = int(instruction[5:-1])
            qc2.x(qr[old_qr])
        elif instruction[0] == 'h':
            old_qr = int(instruction[5:-1])
            qc2.h(qr[old_qr])
        elif instruction[0] == 'm':
            pass
        else:
            raise Exception('Unable to parse instruction')


def encrypt(request):
    n=16

    # Quantum circuit for alice state
    alice = QuantumCircuit(qr, cr, name='Alice')

    # Generate a random number in the range of available qubits [0,65536))
    alice_key = np.random.randint(0, high=2 ** n)

    # Cast key to binary for encoding
    # range: key[0]-key[15] with key[15] least significant figure
    alice_key = np.binary_repr(alice_key, n)  # n is the width

    # Encode key as alice qubits
    # IBM's qubits are all set to |0> initially
    for index, digit in enumerate(alice_key):
        if digit == '1':
            alice.x(qr[index])  # if key has a '1', change state to |1>

    # Switch randomly about half qubits to diagonal basis
    alice_table = []  # Create empty basis table
    for index in range(len(qr)):  # BUG: enumerate(q) raises an out of range error
        if 0.5 < np.random.random():  # With 50% chance...
            alice.h(qr[index])  # ...change to diagonal basis
            alice_table.append('X')  # character for diagonal basis
        else:
            alice_table.append('Z')  # character for computational basis

    # get_qasm method needs the str label
    # alternatively we can use circuits[0] but since dicts are not ordered
    # it is not a good idea to put them in a func
    # circuits = list(qp.get_circuit_names())

    qm = QuantumModel()
    qm.alice = alice
    qm.bob = QuantumCircuit(qr, cr, name='Bob')
    qm.save()

    SendState(qm.alice, qm.bob)

    return JsonResponse({'key': str(qm.key)})
def decrypt(request, hex_code):
    try:
        # Retrieve the QuantumModel object based on the hex_code
        qm = QuantumModel.objects.get(key=hex_code)
    except QuantumModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid hex code'})

    alice_key = request.data['alice_key']
    alice_table = request.data['alice_table']
    bob_table = request.data['bob_table']
    histogram = request.data['histogram']

    keep = []
    discard = []

    for qubit, basis in enumerate(zip(alice_table, bob_table)):
        if basis[0] == basis[1]:
            keep.append(qubit)
        else:
            discard.append(qubit)

    acc = 0
    for bit in zip(alice_key, histogram):
        if bit[0] == bit[1]:
            acc += 1

    new_alice_key = [alice_key[qubit] for qubit in keep]
    new_bob_key = [list(histogram)[0][qubit] for qubit in keep]

    acc = 0
    for bit in zip(new_alice_key, new_bob_key):
        if bit[0] == bit[1]:
            acc += 1

    similarity_percentage = acc / len(new_alice_key)
    is_success = acc == len(new_alice_key)

    return JsonResponse({'new_alice_key': new_alice_key, 'new_bob_key': new_bob_key, 'similarity_percentage': similarity_percentage, 'is_success': is_success})
