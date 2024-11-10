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
    "Turkish": "tr",
}


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
        target = target.lower()
        if ("characters/dialogue" in target or
                "strings/characters" in target or
                "data/engagementdialogue" in target or
                "Data/ExtraDialogue".lower() in target or
                "strings/specialorderstrings" in target or
                "strings/speechbubble" in target or
                "strings/stringsfromcsfiles" in target or
                "strings/stringsfrommaps" in target or
                "strings/locations" in target or
                "strings/schedules" in target or
                "strings/ui" in target or
                "strings/buffs" in target or
                "strings/mail" in target or
                "strings/speechbubbles" in target or
                "strings/animationDescriptions" in target or
                "madamstrings" in target or
                target.startswith("dialogue/") or
                "strings/events" in target):
            return TargetAssetType.PlainText
        elif "data/events/farmhouse" in target:
            return TargetAssetType.EventsLike
        elif "data/quests" in target:
            return TargetAssetType.Quests
        elif "data/events" in target:
            return TargetAssetType.EventsLike
        elif "data/festivals" in target:
            return TargetAssetType.Festivals
        elif "data/npcdispositions" in target:
            return TargetAssetType.NPCDispositions
        elif "data/npcgifttastes" in target:
            return TargetAssetType.NPCGiftTastes
        elif "data/moviesreactions" in target:
            return TargetAssetType.MoviesReactions
        elif "data/mail" in target:
            return TargetAssetType.Mail
        elif "data/objectinformation" in target:
            return TargetAssetType.ObjectInformation
        elif "data/bigcraftablesinformation" in target:
            return TargetAssetType.BigCraftablesInformation
        elif "data/secretnotes" in target:
            return TargetAssetType.SecretNotes
        elif "mods/bouhm.npcmaplocations/locations" == target:
            return TargetAssetType.NPCMapLocations
        elif "data/specialorders" == target:
            return TargetAssetType.DataSpecialOrders
        elif "Data/PassiveFestivals".lower() == target:
            return TargetAssetType.PassiveFestivals
        elif "Data/BigCraftables".lower() == target:
            return TargetAssetType.BigCraftables
        elif "Data/CookingRecipes".lower() in target:
            return TargetAssetType.CookingRecipes
        elif "Data/Objects".lower() in target:
            return TargetAssetType.Objects
        elif "Data/Weapons".lower() in target:
            return TargetAssetType.Weapons
        elif "Data/Locations".lower() in target:
            return TargetAssetType.Locations
        elif "Data/WorldMap".lower() in target:
            return TargetAssetType.WorldMap
        elif "Data/Characters".lower() in target:
            return TargetAssetType.Characters
        elif "Data/JukeboxTracks".lower() in target:
            return TargetAssetType.JukeboxTracks
        elif "Data/Shirts".lower() in target:
            return TargetAssetType.Shirts
        elif "Data/FarmAnimal".lower() in target:
            return TargetAssetType.FarmAnimal
        elif "Data/Hats".lower() in target:
            # {
            #     "LogName": "Hats Data",
            #     "Action": "EditData",
            #     "Target": "Data/Hats",
            #     "Entries": {
            #         "Rafseazz.RSVCP_Occult_Red_Scarf": "Occult Red Scarf/{{i18n:hats.occult-red-scarf.description}}/true/false//{{i18n:hats.occult-red-scarf.name}}/0/RSV\\Objects\\Hats"
            #     }
            # }
            return TargetAssetType.Hats
        elif "Data/Boots".lower() in target:
            return TargetAssetType.Boots
        elif "Data/ClothingInformation".lower() in target:
            return TargetAssetType.ClothingInformation
        elif "Data/Furniture".lower() in target:
            return TargetAssetType.Furniture
        elif "Data/Buildings".lower() in target:
            return TargetAssetType.Buildings
        elif "Data/Minecarts".lower() in target:
            return TargetAssetType.Minecarts
        elif "Data/FruitTrees".lower() in target:
            return TargetAssetType.FruitTrees
        elif "Data/Pants".lower() in target:
            return TargetAssetType.Pants
        elif "Data/CraftingRecipes".lower() in target:
            return TargetAssetType.CraftingRecipes
        elif "Mods/CJBok.CheatsMenu".lower() in target:
            return TargetAssetType.CheatsMenu
        elif "UnlockableBundles/Bundles".lower() in target:
            return TargetAssetType.Bundles
        elif "Data/Shops".lower() in target:
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
