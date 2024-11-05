# Transtar
Stardew Valley Mod Translation Tool

星露谷物语 MOD 翻译工具

If my tool has been helpful for your translation work, I would appreciate it if you could consider adding a link to it on the homepage of your translation mod. This would make me feel that my efforts have not been in vain and that there are people using it.

## Feature

* Extract mod entry, therefore, you do not need to understand various framework formats.
* Extract sentence in CP file and not in i18n file（The mod author can be used to check if there are any missing sentences that have not been placed in the i18n file）
* The entire process from extraction to generating the final translation file.
* Verify if there are any omissions or losses in the translated text, such as %farm, $1, ^, #.
* Support machine translate

## Who needs to use it
* Mod translators or teams translating a large number of mods.
## How to use
### Install
1. Only support windows.
2. Download and unzip the file to a separate folder.
3. Run transtar.exe and select your language.
4. Drop the mod folder that you want to translate into the drop area or select the folder manually.

### Extract
1. Click the extract button, and a 'dict' folder will be generated, containing the content that requires translation.

### Extract old
> Do not plagiarize another author's translation by using the 'Extract old' without authorization from the original translator.
> 
> If you already have a dict file, you don't need to use this feature, you just need to click extract when updating
* Click extract old button.
* Select the original mod folder of the old version and the folder of the old version of the mod with the translation already installed.
* Click Execute button.

### Translate
1. Click translate button.
2. When it has finished. choose a way to optimize translation
   * First way: Open the "dict" folder, and open each JSON file in "dict" folder, replace the content in the "translation" field of each entry with the better translated sentences.
   * Second way:  upload the content from the "dict" files to https://paratranz.cn/, which is a collaborative translation platform for managing changes to our entries and facilitating team-based translation.﻿
> Tips:
  If one wants to use ParaTranz. First, you need to have a GitHub account to log in to the ParaTranz website, then you need to create a project of your own , and then you can upload the "dict" folder or files to this website to translate.

> 遇到cannot unpack non-iterabled nonetype object这个报错是你网络访问不了Google翻译。要开梯子，没有梯子的话，你可以把dict文件直接上传协作平台，然后自己在浏览器上翻，或者直接打开dict文件夹里面的内容，把translation属性替换成中文。）

### Check

1. check that your 'dict' folder exists and that its contents have been translated
2. click Check button
3. if success will notice
4. if error will pop a folder named error,check files in it.
5. fix the error in dict file until no error. Some error may be ignored if is moder error.

### Generate
1. check that your 'dict' folder exists and that its contents have been translated
2. If you used the second way to translate, you just need to download the files you uploaded and place them back into the 'dict' folder.
3. Drop your mod folder （not dict folder）to drop area
4. click Generate button
5. After completing the generation, a mod translation package will be generated

## Support framework
1. [CP] Content Patcher
2. [i18n] i18n/default.json
3. [JA] Json Assets(mod deprecated)
4. [MFM] Mail Framework Mod(mod deprecated)
5. [STF] Shop Tile Framework(mod deprecated)
6. [QF] Quest Framework(mod deprecated)

