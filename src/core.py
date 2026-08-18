# Disable __pycache__
import sys
sys.dont_write_bytecode = True

import os
import struct
from pathlib import Path
import base64

from PIL import Image
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from constants import MAGIC_LSB, MAGIC_APP, END_APP, ENCRYPT_MARKER


# ===== CRYPTO =====

def derive_key(password: str, salt: bytes = None) -> tuple:
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_data(data: bytes, password: str) -> bytes:
    key, salt = derive_key(password)
    f = Fernet(key)
    return salt + f.encrypt(data)


def decrypt_data(encrypted_data: bytes, password: str) -> bytes:
    salt = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    key, _ = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(ciphertext)


def is_encrypted(payload: bytes) -> bool:
    """Check if payload is encrypted"""
    return payload.startswith(ENCRYPT_MARKER)


# ===== LSB STEGANOGRAPHY =====

def hide_lsb(image_path: str, file_path: str, output_path: str, password: str = None) -> bool:
    file_path = Path(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()

    if password:
        encrypted_data = encrypt_data(file_data, password)
        file_name = file_path.name.encode('utf-8')
        payload = ENCRYPT_MARKER + struct.pack('>H', len(file_name)) + file_name + encrypted_data
    else:
        file_name = file_path.name.encode('utf-8')
        payload = struct.pack('>H', len(file_name)) + file_name + file_data

    header = MAGIC_LSB + struct.pack('>I', len(payload)) + payload

    img = Image.open(image_path)
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert('RGB')
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    pixels = list(img.getdata())
    capacity = len(pixels) * 1 if img.mode == 'L' else len(pixels) * 3
    bits_needed = len(header) * 8

    if bits_needed > capacity:
        raise Exception(f"File too large. Max: {capacity//8} bytes")

    bits = []
    for byte in header:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    new_pixels = []
    bit_idx = 0
    for pixel in pixels:
        if img.mode == 'L':
            if bit_idx < len(bits):
                new_pixels.append((pixel & 0xFE) | bits[bit_idx])
                bit_idx += 1
            else:
                new_pixels.append(pixel)
        else:
            r, g, b = pixel[:3]
            if bit_idx < len(bits):
                r = (r & 0xFE) | bits[bit_idx]
                bit_idx += 1
            if bit_idx < len(bits):
                g = (g & 0xFE) | bits[bit_idx]
                bit_idx += 1
            if bit_idx < len(bits):
                b = (b & 0xFE) | bits[bit_idx]
                bit_idx += 1
            new_pixels.append((r, g, b))

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path)
    return True


def extract_lsb(image_path: str) -> bytes:
    img = Image.open(image_path)
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert('RGB')
    pixels = list(img.getdata())

    bits = []
    for pixel in pixels:
        if img.mode == 'L':
            bits.append(pixel & 1)
        else:
            bits.append(pixel[0] & 1)
            bits.append(pixel[1] & 1)
            bits.append(pixel[2] & 1)

    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
            else:
                byte = byte << 1
        data.append(byte)

    data = bytes(data)
    pos = data.find(MAGIC_LSB)
    if pos == -1:
        return None

    idx = pos + len(MAGIC_LSB)
    payload_len = struct.unpack('>I', data[idx:idx+4])[0]
    idx += 4
    return data[idx:idx+payload_len]


# ===== APPEND STEGANOGRAPHY =====

def hide_append(image_path: str, file_path: str, output_path: str, password: str = None) -> bool:
    file_path = Path(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()

    if password:
        encrypted_data = encrypt_data(file_data, password)
        file_name = file_path.name.encode('utf-8')
        payload = ENCRYPT_MARKER + struct.pack('>H', len(file_name)) + file_name + encrypted_data
    else:
        file_name = file_path.name.encode('utf-8')
        payload = struct.pack('>H', len(file_name)) + file_name + file_data

    with open(image_path, 'rb') as f:
        image_data = f.read()

    full_payload = MAGIC_APP + struct.pack('>I', len(payload)) + payload + END_APP

    with open(output_path, 'wb') as f:
        f.write(image_data)
        f.write(full_payload)
    return True


def extract_append(image_path: str) -> bytes:
    with open(image_path, 'rb') as f:
        data = f.read()

    start = data.find(MAGIC_APP)
    if start == -1:
        return None

    idx = start + len(MAGIC_APP)
    payload_len = struct.unpack('>I', data[idx:idx+4])[0]
    idx += 4
    return data[idx:idx+payload_len]


# ===== UTILITY =====

def process_payload(payload: bytes, password: str = None) -> tuple:
    if is_encrypted(payload):
        if not password:
            raise Exception("Password required")
        idx = len(ENCRYPT_MARKER)
        name_len = struct.unpack('>H', payload[idx:idx+2])[0]
        idx += 2
        file_name = payload[idx:idx+name_len].decode('utf-8')
        idx += name_len
        return file_name, decrypt_data(payload[idx:], password)
    else:
        name_len = struct.unpack('>H', payload[:2])[0]
        idx = 2
        file_name = payload[idx:idx+name_len].decode('utf-8')
        idx += name_len
        return file_name, payload[idx:]


def save_file(file_name: str, file_data: bytes, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    original = Path(file_name)
    extracted_name = f"{original.stem}_extracted{original.suffix}"
    path = out / extracted_name

    counter = 1
    while path.exists():
        path = out / f"{original.stem}_{counter}{original.suffix}"
        counter += 1

    with open(path, 'wb') as f:
        f.write(file_data)
    return path