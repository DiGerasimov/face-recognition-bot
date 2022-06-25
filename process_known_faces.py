import pathlib
import sys
from typing import Tuple, List, Literal

import face_recognition


CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
KNOWN_FACES_DIR = CURRENT_DIR / 'photos'


JPG_PHOTOS: List[pathlib.Path] = list(KNOWN_FACES_DIR.rglob('*.jpg'))
PNG_PHOTOS: List[pathlib.Path] = list(KNOWN_FACES_DIR.rglob('*.png'))

ALL_PHOTOS = JPG_PHOTOS + PNG_PHOTOS


def process_known_faces(write_mode: Literal['w', 'a'] = 'a'):
    if write_mode == 'w':
        filenames: List[str] = []
        faces: List[Tuple[float, ...]] = []
    elif write_mode == 'a':
        try:
            from application.known_faces import known_faces as old_known_faces
        except ImportError:
            old_known_faces = ((), ())

        filenames: List[str] = list(old_known_faces[0])
        faces: List[Tuple[float, ...]] = list(old_known_faces[1])
    else:
        raise ValueError

    count = len(ALL_PHOTOS)

    try:
        for number, filename in enumerate(ALL_PHOTOS, 1):
            filename = str(filename)

            if str(filename) in filenames:
                print(f'Skipped | {number}/{count} | {filename = }')
                continue

            image = face_recognition.load_image_file(KNOWN_FACES_DIR / filename)

            faces_encodings = face_recognition.face_encodings(
                face_image=image, num_jitters=1, model="small"
            )

            for face_encoding in faces_encodings:
                filenames.append(str(KNOWN_FACES_DIR / filename))
                faces.append(tuple(face_encoding))

            status = 'Converted' if faces_encodings else 'No faces detected'

            print(f'{status} | {number}/{count} | {filename = }')

        _known_faces = tuple(filenames), tuple(faces)

        with open(CURRENT_DIR / 'application' / 'known_faces.py', 'w') as f:
            f.write('known_faces = ' + str(_known_faces))
    except KeyboardInterrupt:
        answer = input(f'Хотите сохранить изменения: {len(filenames)} файлов ? (Y/N)')

        if answer.lower() == 'n':
            return

        _known_faces = tuple(filenames), tuple(faces)

        with open(CURRENT_DIR / 'application' / 'known_faces.py', 'w') as f:
            f.write('known_faces = ' + str(_known_faces))


if __name__ == '__main__':
    DEFAULT_MODE = 'a'

    try:
        mode = sys.argv[1]
    except IndexError:
        mode = DEFAULT_MODE

    print(sys.argv)

    process_known_faces(mode)  # type: ignore
