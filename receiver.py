import aioble
import bluetooth
import asyncio
import struct
import time
from sys import exit
from machine import Pin, ADC, UART, PWM

_SERVICE_UUID = bluetooth.UUID(0x1848)
_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)

IAM = "Receiver"
IAM_SENDING_TO = "Sender"
MESSAGE = f"Hello from {IAM}!"

BLE_NAME = f"{IAM}"
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 30000
BLE_WINDOW = 30000

message_count = 0



def encode_message(message):
    """ Encode a message to bytes """
    return message.encode('utf-8')

def decode_message(message):
    """Decode a message from bytes """
    return message.decode('utf-8')


        
async def receive_data_task(characteristic):
    """ Receive data from the connected device """
    global message_count
    servo = PWM(Pin(16))  # Servo connected to GP15
    servo.freq(50)
    while True:
        try:
            data = await characteristic.read()
            
            if data:
                print(f"{IAM} received: {decode_message(data)}, count: {message_count}")
                servo.duty_u16(data)
                #await characteristic.write(encode_message("Got it"))
                await asyncio.sleep(0.5)
                
            message_count += 1
            
        except asyncio.TimeoutError:
            print("Timeout waiting for data in {ble_name}.")
            break
        except Exception as e:
            print(f"Error receiving data: {e}")
            break
        

             
async def ble_scan():
    """ Scan for a BLE device with the matching service UUID """
    
    print(f"Scanning for BLE Beacon named {BLE_NAME}...")
    
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == IAM_SENDING_TO and BLE_SVC_UUID in result.services():
                print(f"found {result.name()} with service uuid {BLE_SVC_UUID}")
                return result
    return None

async def run_receiver_mode():
    """ Run the central mode """
    
    while True:
        device = await ble_scan()
        
        if device is None:
            continue
        print(f"device is : {device}, name is: {device.name()}")
        
        try:
            print(f"Connecting to {device.name()}")
            connection = await device.device.connect()
            
        except asyncio.TimeoutError:
            print("Timeout during connection")
            continue
        
        print(f"{IAM} connected to {connection}")
        
        async with connection:
            try:
                service = await connection.service(BLE_SVC_UUID)
                characteristic = await service.characteristic(BLE_CHARACTERISTIC_UUID)
            except (asyncio.TimeoutError, AttributeError):
                print("Timed out discovering services/characteristics")
                continue
            except Exception as e:
                print(f"Error discovering services {e}")
                await connection.disconnect()
                continue
            
            tasks = [
                asyncio.create_task(receive_data_task(characteristic)),
            ]
            await asyncio.gather(*tasks)
            
            await connection.disconnected()
            print(f"{BLE_NAME} disconnected from {device.name()}")
            break
    
async def main():
    """ Main function """
    while True:
        if IAM == "Receiver":
            tasks = [
                asyncio.create_task(run_receiver_mode()),
            ]
        else:
            tasks = [
                asyncio.create_task(run_peripheral_mode()),
            ]
        
        await asyncio.gather(*tasks)
        
asyncio.run(main())


