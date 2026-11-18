# GMaps Scout

Turn publicly listed business details into a spreadsheet for market research.

**Try it online:** [lab.vulpfest.com/gmapscout](https://lab.vulpfest.com/gmapscout), part of [Vulpfest Lab](https://lab.vulpfest.com), free and open-source tools from Vulpfest.

## What it does

- Search by type of business and location, with a limit on how many results to collect.
- Collects publicly listed details such as name, category, address, business phone and rating.
- Download the results as an Excel or CSV file.

## Run it yourself

````bash
git clone https://github.com/FebriOsht/gmap-scout.git
cd gmap-scout
pip install -r requirements.txt
streamlit run app_scraper.py
```

Needs Google Chrome or Chromium on your computer. On Streamlit Community Cloud, Chromium is installed from `packages.txt`.

## Command line

Requires Google Chrome or Chromium.

```bash
pip install selenium webdriver-manager pandas xlsxwriter openpyxl
python cli.py "coffee shop in Bali" --limit 20 --out leads.xlsx
python cli.py "coffee shop in Bali" --limit 20 --out leads.csv
```

| Option | Meaning |
|---|---|
| `query` | what to search for on Google Maps (required) |
| `--limit` | maximum number of places, 1 to 200 (default 20) |
| `--out` | save as `.xlsx` or `.csv`; without it, results are printed to the terminal |
| `--show-browser` | show the browser window instead of running headless |

## Responsible use

Collect only publicly listed business information. Automated collection from Google Maps may conflict with Google's Terms of Service; you are responsible for following the terms of the websites you use and data protection laws such as Indonesia's Personal Data Protection Law (UU PDP). For production use, consider the official Google Places API.

The software is provided as is, without warranty. You are responsible for how you use it and for any data you collect.

## Security

Found a security issue? Please see [SECURITY.md](SECURITY.md).

## License

MIT © 2026 Febri Osht (Vulpfest). See [LICENSE](LICENSE).