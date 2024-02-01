from base64 import b64decode, b64encode
from io import BytesIO
import json
from typing import Any, Final, TypedDict
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent


class TranslationType(TypedDict):
    lang: str
    text: str

class TranslatableType(TypedDict):
    id: str
    translations: list[TranslationType]

class SkinpackType(TranslatableType):
    name: str

class SkinType(TranslatableType):
    image: str

class RequestBodyType(TypedDict):
    skinpack: SkinpackType
    skins: list[SkinType]


class JsonFileContent:
    FILE_PATH: str

    def __init__(self) -> None:
        self.dct: dict

    def dump(self, zf: ZipFile):
        zf.writestr(self.FILE_PATH, json.dumps(self.dct, indent=4))


class ManifestFileContent(JsonFileContent):
    FILE_PATH: Final[str] = 'manifest.json'

    def __init__(self, skinpack: SkinpackType) -> None:
        self.dct = {
            'format_version': 2,
            'header': {
                'name': skinpack['name'],
                'version': [1, 0, 0],
                'uuid': str(uuid4())
            },
            'modules': [
                {
                    'version': [1, 0, 0],
                    'type': 'skin_pack',
                    'uuid': str(uuid4())
                }
            ]
        }


class SkinListFileContent(JsonFileContent):
    FILE_PATH: Final[str] = 'skins.json'
    GEOMETRY_TYPES: Final[tuple[str, ...]] = (
        'geometry.humanoid.custom',
        'geometry.humanoid.customSlim'
    )

    def __init__(self, skinpack: SkinpackType) -> None:
        self.dct = {
            'serialize_name': skinpack['name'],
            'localization_name': skinpack['id'],
            'skins': []
        }
    
    def add_skin(self, skin: SkinType) -> None:
        for geometry_type in self.GEOMETRY_TYPES:
            self.dct['skins'].append({
                'localization_name': skin['id'],
                'geometry': geometry_type,
                'texture': f'{skin["id"]}.png',
                'type': 'free'
            })


class TranslationFilesContent:
    """
    [
        "skinpack.skinpackIdOne": "Skinpack Name 1",
        "skin.skinpackIdOne.skinIdOne": "Skin Name 1",
        "skin.skinpackIdOne.skinIdTwo": "Skin Name 2",
        ...
    ]
    """
    def __init__(self, skinpack: SkinpackType) -> None:
        self.skinpack_id = skinpack['id']
        self.lst: list = []
        self._add_skinpack(skinpack)

    def _add(self, item: TranslatableType, key_before_id: str) -> None:
        for translation in item['translations']:
            if not self.lst or next(filter(lambda k: k['lang'] == translation['lang'], self.lst), None) is None:
                self.lst.append({
                    'lang': translation['lang'],
                    'translations': {}
                })
            idx = [idx for idx, val in enumerate(self.lst) if val['lang'] == translation['lang']][0]
            self.lst[idx]['translations'][f'{key_before_id}.{item["id"]}'] = translation['text']

    def _add_skinpack(self, skinpack: SkinpackType) -> None:
        self._add(skinpack, 'skinpack')

    def add_skin(self, skin: SkinType) -> None:
        self._add(skin, f'skin.{self.skinpack_id}')

    def dump(self, zf: ZipFile) -> None:
        for translation_per_lang in self.lst:
            zf.writestr(f'texts/{translation_per_lang["lang"]}.lang', '\n'.join([f'{key}={value}' for key, value in translation_per_lang['translations'].items()]))


app = APIGatewayRestResolver()

@app.post('/skinpacks')
def create_skinpack():
    data: RequestBodyType = app.current_event.body
    skinpack = data['skinpack']
    skins = data['skins']

    manifest_file_content = ManifestFileContent(skinpack)
    skin_list_file_content = SkinListFileContent(skinpack)
    translation_file_content = TranslationFilesContent(skinpack)

    zs = BytesIO()
    with ZipFile(zs, 'w', compression=ZIP_DEFLATED) as zf:
        manifest_file_content.dump(zf)

        for skin in skins:
            skin_list_file_content.add_skin(skin)
            translation_file_content.add_skin(skin)
            zf.writestr(f'{skin["id"]}.png', b64decode(skin['image']))

        skin_list_file_content.dump(zf)
        translation_file_content.dump(zf)

    # b64encodeはbytesを返すのでstrに変換する必要がある
    return {'name': f'{skinpack["id"]}.mcpack', 'content': b64encode(zs.getvalue()).decode('utf-8')}


def handler(event: APIGatewayProxyEvent, context: LambdaContext) -> dict[str, Any]:
    return app.resolve(event, context)
