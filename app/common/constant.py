from enum import Enum

CONFIG_FILE = "config.json"

LANGUAGES = {
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Hungarian": "hu",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Thai": "th",
    "Turkish": "tr",
    "Vietnamese": "vi",
    "Bahasa Indonesia": "id",
    "Polish": "pl"
}

LANGUAGE_KEY_NAME = {v: k for k, v in LANGUAGES.items()}


class ActionType(Enum):
    EXTRACT = 1
    GENERATE = 2
    VALIDATE = 3
    TRANSLATE = 4
    IMPORT_ERROR = 5


class FileType(Enum):
    UNKNOWN = "UNKNOWN"
    JA = "JA.json"
    CP = "CP.json"
    I18N = "i18n.json"
    MAIL = "mail.json"
    BL = "BL.json"
    STF = "STF.json"
    QF = "QF.json"

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name


class TargetAssetType(Enum):
    Bundles = "Bundles"
    Pants = "Pants"
    CheatsMenu = "CheatsMenu"
    PlainText = "PlainText"
    EventsLike = "EventsLike"
    Festivals = "Festivals"
    NPCDispositions = "NPCDispositions"
    NPCGiftTastes = "NPCGiftTastes"
    MoviesReactions = "MoviesReactions"
    MarriageMoviesReactions = "MarriageMoviesReactions"
    Mail = "Mail"
    ObjectInformation = "ObjectInformation"
    BigCraftablesInformation = "BigCraftablesInformation"
    Quests = "Quests"
    SecretNotes = "SecretNotes"
    Unknown = "Unknown"
    NPCMapLocations = "NPCMapLocations"
    DataSpecialOrders = "DataSpecialOrders"
    Locations = "Locations"
    PassiveFestivals = "PassiveFestivals"
    BigCraftables = "BigCraftables"
    CookingRecipes = "CookingRecipes"
    CraftingRecipes = "CraftingRecipes"
    Objects = "Objects"
    Weapons = "Weapons"
    WorldMap = "WorldMap"
    Characters = "Characters"
    JukeboxTracks = "JukeboxTracks"
    Shirts = "Shirts"
    Hats = "Hats"
    Boots = "Boots"
    ClothingInformation = "ClothingInformation"
    Furniture = "Furniture"
    Clothing = "Clothing"
    Buildings = "Buildings"
    Minecarts = "Minecarts"
    Shops = "Shops"
    FarmAnimal = "FarmAnimal"
    FruitTrees = "FruitTrees"

    @staticmethod
    def get_target_asset_type(target):
        target_lower = target.lower()
        if ("characters/dialogue" in target_lower or
                "strings/characters" in target_lower or
                "data/engagementdialogue" in target_lower or
                "Data/ExtraDialogue".lower() in target_lower or
                "strings/specialorderstrings" in target_lower or
                "strings/speechbubble" in target_lower or
                "strings/stringsfromcsfiles" in target_lower or
                "strings/stringsfrommaps" in target_lower or
                "strings/locations" in target_lower or
                "strings/schedules" in target_lower or
                "strings/ui" in target_lower or
                "strings/buffs" in target_lower or
                "strings/mail" in target_lower or
                "strings/speechbubbles" in target_lower or
                "strings/animationDescriptions" in target_lower or
                "madamstrings" in target_lower or
                target_lower.startswith("dialogue/") or
                "strings/events" in target_lower):
            return TargetAssetType.PlainText
        elif "data/events/farmhouse" in target_lower:
            return TargetAssetType.EventsLike
        elif "data/quests" in target_lower:
            return TargetAssetType.Quests
        elif "data/events" in target_lower:
            return TargetAssetType.EventsLike
        elif "data/festivals" in target_lower:
            return TargetAssetType.Festivals
        elif "data/npcdispositions" in target_lower:
            return TargetAssetType.NPCDispositions
        elif "data/npcgifttastes" in target_lower:
            return TargetAssetType.NPCGiftTastes
        elif "data/moviesreactions" in target_lower:
            return TargetAssetType.MoviesReactions
        elif "data/mail" in target_lower:
            return TargetAssetType.Mail
        elif "data/objectinformation" in target_lower:
            return TargetAssetType.ObjectInformation
        elif "data/bigcraftablesinformation" in target_lower:
            return TargetAssetType.BigCraftablesInformation
        elif "data/secretnotes" in target_lower:
            return TargetAssetType.SecretNotes
        elif "mods/bouhm.npcmaplocations/locations" == target_lower:
            return TargetAssetType.NPCMapLocations
        elif "data/specialorders" == target_lower:
            return TargetAssetType.DataSpecialOrders
        elif "Data/PassiveFestivals".lower() == target_lower:
            return TargetAssetType.PassiveFestivals
        elif "Data/BigCraftables".lower() == target_lower:
            return TargetAssetType.BigCraftables
        elif "Data/CookingRecipes".lower() in target_lower:
            return TargetAssetType.CookingRecipes
        elif "Data/Objects".lower() in target_lower:
            return TargetAssetType.Objects
        elif "Data/Weapons".lower() in target_lower:
            return TargetAssetType.Weapons
        elif "Data/Locations".lower() in target_lower:
            return TargetAssetType.Locations
        elif "Data/WorldMap".lower() in target_lower:
            return TargetAssetType.WorldMap
        elif "Data/Characters".lower() in target_lower:
            return TargetAssetType.Characters
        elif "Data/JukeboxTracks".lower() in target_lower:
            return TargetAssetType.JukeboxTracks
        elif "Data/Shirts".lower() in target_lower:
            return TargetAssetType.Shirts
        elif "Data/FarmAnimal".lower() in target_lower:
            return TargetAssetType.FarmAnimal
        elif "Data/Hats".lower() in target_lower:
            # {
            #     "LogName": "Hats Data",
            #     "Action": "EditData",
            #     "Target": "Data/Hats",
            #     "Entries": {
            #         "Rafseazz.RSVCP_Occult_Red_Scarf": "Occult Red Scarf/{{i18n:hats.occult-red-scarf.description}}/true/false//{{i18n:hats.occult-red-scarf.name}}/0/RSV\\Objects\\Hats"
            #     }
            # }
            return TargetAssetType.Hats
        elif "Data/Boots".lower() in target_lower:
            return TargetAssetType.Boots
        elif "Data/ClothingInformation".lower() in target_lower:
            return TargetAssetType.ClothingInformation
        elif "Data/Furniture".lower() in target_lower:
            return TargetAssetType.Furniture
        elif "Data/Buildings".lower() in target_lower:
            return TargetAssetType.Buildings
        elif "Data/Minecarts".lower() in target_lower:
            return TargetAssetType.Minecarts
        elif "Data/FruitTrees".lower() in target_lower:
            return TargetAssetType.FruitTrees
        elif "Data/Pants".lower() in target_lower:
            return TargetAssetType.Pants
        elif "Data/CraftingRecipes".lower() in target_lower:
            return TargetAssetType.CraftingRecipes
        elif "Mods/CJBok.CheatsMenu".lower() in target_lower:
            return TargetAssetType.CheatsMenu
        elif "UnlockableBundles/Bundles".lower() in target_lower:
            return TargetAssetType.Bundles
        elif "Data/Shops".lower() in target_lower:
            # {
            #     "Action": "EditData",
            #     "Target": "Data/Shops",
            #     "Entries": {
            #         "FlashShifter.StardewValleyExpandedCP_ChloeVendor1": {
            #             "Owners": [
            #                 {
            #                     "Name": "AnyOrNone",
            #                     "Portrait": "{{InternalAssetKey: assets/CharacterFiles/Shops/Joja/Chloe_Vendor.png}}",
            #                     "Dialogues": [
            #                             {
            #                                 "Id": "FlashShifter.StardewValleyExpandedCP_JojaDay_Default",
            #                                 "Dialogue": "{{i18n:ShopsDialogue.ClaireJoja}}",
            #                                 "Condition": "IS_PASSIVE_FESTIVAL_TODAY FlashShifter.StardewValleyExpandedCP_JojaDay"
            #                             },
            #                             {
            #                                 "Id": "FlashShifter.StardewValleyExpandedCP_Default",
            #                                 "Dialogue": "{{i18n:ShopsDialogue.Claire}}",
            #                             }
            #                      ]
            #                 }
            #             ],
            #             "Items": [
            #                 {
            #                     "Id": "FlashShifter.StardewValleyExpandedCP_Magic_Rock_Candy",
            #                     "ItemId": "279",
            #                     "Price": 85000,
            #                     "AvailableStock": 1
            #                 }
            #             ]
            #         }
            #     }
            # }
            return TargetAssetType.Shops
        else:
            return TargetAssetType.Unknown


if __name__ == '__main__':
    print(LANGUAGES.values())
    print(ActionType.EXTRACT)
