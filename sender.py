import aioble
import bluetooth
import asyncio
import struct
from sys import exit
from machine import Pin, ADC, UART
import time

_SERVICE_UUID = bluetooth.UUID(0x1848)
_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)

IAM = "Sender"
IAM_SENDING_TO = "Receiver"
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

async def send_data_task(connection, characteristic):
    """ Send data to the connected device """
    global message_count
    potentiometer = ADC(Pin(26))
    while True:
        if not connection:
            print("error - no connection in send data")
            continue
        if not characteristic:
            print("error no characteristic provided in send data")
            continue
        
        pot_value = potentiometer.read_u16()
        angle = (pot_value / 65535) * 180
        min_duty = 1000
        max_duty = 9000
        duty = int(min_duty + (max_duty - min_duty) * angle / 180)
        dutyStr = str(duty)
        message = f"Duty: {duty} {message_count}"
        message_count += 1
        #print(f"sending {message}")
        
        try:
            msg = encode_message(message)
            characteristic.write(msg)
            
            await asyncio.sleep(0.1)
            
            
            print(f"{IAM} sent: {message}")
        except Exception as e:
            print(f"writing error {e}")
            continue
        
        await asyncio.sleep(0.5)
        

async def run_sender_mode():
    """ Run the peripheral mode """
    
    
    ble_service = aioble.Service(BLE_SVC_UUID)
    characteristic = aioble.Characteristic(
        ble_service,
        BLE_CHARACTERISTIC_UUID,
        read=True,
        notify=True,
        write=True,
        capture=True,
    )
    aioble.register_services(ble_service)
    
    print(f"{BLE_NAME} starting to advertise")
    
    while True:
        async with await aioble.advertise(
            BLE_ADVERTISING_INTERVAL,
            name=BLE_NAME,
            services=[BLE_SVC_UUID],
            appearance=BLE_APPEARANCE) as connection:
            print(f"{BLE_NAME} connected to another device: {connection.device}")
            
            task = [
                asyncio.create_task(send_data_task(connection, characteristic))
            ]
            await asyncio.gather(*task)
            print(f"{IAM} disconnected")
            break
                                    
async def ble_scan():
    """ Scan for a BLE device with the matching service UUID """
    
    print(f"Scanning for BLE Beacon named {BLE_NAME}...")
    
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True):
        async for result in scanner:
            if result.name() == IAM_SENDING_TO and BLE_SVC_UUID in result.service:
                print(f"found {result.name()} with service uuid {BLE_SVC_UUID}")
                return result
    return None


    
async def main():
    """ Main function """
    while True:
        if IAM == "Sender":
            tasks = [
                asyncio.create_task(run_sender_mode()),
            ]
        else:
            tasks = [
                asyncio.create_task(run_peripheral_mode()),
            ]
        
        await asyncio.gather(*tasks)
        
asyncio.run(main())




