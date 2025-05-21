import serial
import time

# COM8 = Pico A (voltage)
# COM11 = XRP Pico (servo receiver)

pico_a = serial.Serial('COM8', 115200, timeout=1)
xrp_pico = serial.Serial('COM11', 115200, timeout=1)

print("🔁 Relaying from Pico A (COM8) → XRP Pico (COM11)")

while True:
    try:
        # Read from Pico A
        line = pico_a.readline().decode().strip()

        if line.startswith("DUTY:"):
            print("📤 From Pico A:", line)

            # Forward to XRP Pico
            xrp_pico.write((line + "\n").encode())

            # Give the XRP Pico a moment to respond
            time.sleep(0.1)

            # Read ACK from XRP
            while xrp_pico.in_waiting:
                ack = xrp_pico.readline().decode().strip()
                if ack:
                    print("✅ XRP ACK:", ack)

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(1)
