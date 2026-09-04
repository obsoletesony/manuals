# Japanese manual fonts

The Japanese PSPMAN User's Guide uses subsets of Noto Sans JP, licensed under the SIL Open Font License 1.1.

The source font is the variable `NotoSansJP[wght].ttf` published by the Google Fonts project. Regenerate both committed subsets whenever Japanese manual copy introduces new characters:

```sh
python3 manuals/pspman/source/build_japanese_fonts.py /path/to/NotoSansJP-wght.ttf
```

The builder registers the regular and bold subsets under the same internal ReportLab aliases used by the English layout. This keeps both editions on the same measured page system without changing the English PDF.
