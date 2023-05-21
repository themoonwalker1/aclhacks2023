import RPi.GPIO as GPIO
import time

# Set the GPIO mode and pin number
GPIO.setmode(GPIO.BCM)
PWM_PIN = 18

# Set the frequency and initial duty cycle
PWM_FREQUENCY = 1000  # Adjust this value based on your motor controller's specifications
INITIAL_DUTY_CYCLE = 0  # Adjust this value to set the initial motor speed

# Set up the PWM pin
GPIO.setup(PWM_PIN, GPIO.OUT)
pwm = GPIO.PWM(PWM_PIN, PWM_FREQUENCY)

# Start the PWM with the initial duty cycle
pwm.start(INITIAL_DUTY_CYCLE)

try:
    while True:
        # Prompt the user to enter a duty cycle value
        duty_cycle = float(input("Enter duty cycle (0.0 to 100.0): "))

        # Check if the entered duty cycle is within the valid range
        if 0.0 <= duty_cycle <= 100.0:
            # Change the duty cycle of the PWM signal
            pwm.ChangeDutyCycle(duty_cycle)
        else:
            print("Invalid duty cycle value. Please try again.")

except KeyboardInterrupt:
    # Clean up GPIO on program exit
    pwm.stop()
    GPIO.cleanup()
