import pathlib
from io import BytesIO
from typing import Generator

import face_recognition
import numpy
from PIL import Image

try:
    from known_faces import known_faces  # NOQA
except Exception as e:  # NOQA
    print("Can't import `known faces`:")
    print("Convert photos!")
    exit(1)


CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
KNOWN_FACES_DIR = CURRENT_DIR.parent / 'photos'


def load_image_from_bytes(bytes_: BytesIO, mode: str = 'RGB') -> numpy.ndarray:
    image: Image.Image = Image.open(bytes_)
    image.convert(mode=mode)

    return numpy.array(image)  # type: ignore


def find_clones(image: numpy.ndarray, tolerance: float = 0.6) -> Generator[str, None, None]:
    for face_image_encodings in face_recognition.face_encodings(image):
        face_distances = face_recognition.face_distance(
            known_faces[1], face_image_encodings
        )

        for filename, is_clone in zip(known_faces[0], face_distances < tolerance):  # type: str, bool
            if is_clone:
                yield filename
