
import asyncio
import serial
from bleak import BleakClient, BleakScanner
from pynput import keyboard

UART_SERVICE_UUID = "27df26c5-83f4-4964-bae0-d7b7cb0a1f54"
UART_RX_UUID = "452af57e-ad27-422c-88ae-76805ea641a9"

COM_PORT = "COM8"
BAUD_RATE = 115200

# Global joystick state
joystick_x = 127
joystick_y = 127

# Clamp function
def clamp(val, min_val=0, max_val=180):
    return max(min_val, min(max_val, val))

# Arrow key handlers
def on_press(key):
    global joystick_x, joystick_y
    try:
        if key == keyboard.Key.up:
            joystick_y = 0
        elif key == keyboard.Key.down:
            joystick_y = 255
        elif key == keyboard.Key.left:
            joystick_x = 0
        elif key == keyboard.Key.right:
            joystick_x = 255
    except:
        pass

def on_release(key):
    global joystick_x, joystick_y
    if key in [keyboard.Key.up, keyboard.Key.down]:
        joystick_y = 127
    if key in [keyboard.Key.left, keyboard.Key.right]:
        joystick_x = 127

async def main():
    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # Open serial to Pico A
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"📡 Listening to {COM_PORT} for voltage data...")
    except Exception as e:
        print("❌ Serial connection failed:", e)
        return

    # Scan and connect to XRProbot
    print("🔍 Scanning for XRProbot...")
    device = await BleakScanner.find_device_by_name("XRProbot")
    if not device:
        print("❌ XRProbot not found.")
        return

    print(f"✅ Found: {device.name} ({device.address})")
    async with BleakClient(device) as client:
        print("🔗 Connected to XRP")

        while True:
            try:
                line = ser.readline().decode().strip()
                if not line.startswith("DUTY:"):
                    continue

                duty = int(line[5:].strip())
                duty = clamp(duty)

                report = bytearray(20)
                report[0] = 0x01
                report[1] = joystick_x
                report[2] = joystick_y
                report[7] = duty

                await client.write_gatt_char(UART_RX_UUID, report)
                print(f"📤 Sent: DUTY:{duty} | JoyX:{joystick_x} JoyY:{joystick_y}")

            except Exception as e:
                print("⚠️ Error:", e)
                await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Exiting.")
