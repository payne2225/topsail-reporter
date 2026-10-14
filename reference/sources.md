# Daily Sources for the Topsail Reporter

Tested with WebFetch on 2026-10-14 (afternoon ET). Status: WORKS / BLOCKED / NO CURRENT CONTENT.
Rule for the routine: if a WORKS source fails on a given morning, say so in the edition; never fill the gap from memory.

## Fishing reports
| Status | URL to fetch | What it carries |
|---|---|---|
| WORKS | https://www.fishermanspost.com/category/fishing-reports/topsail-sneads-ferry/ | Index of monthly Topsail/Sneads Ferry reports (posted on or about the 1st). Newest link at top. |
| WORKS | https://www.fishermanspost.com/topsail-sneads-ferry-october-2026/ | Oct 1, 2026 report: East Coast Sports, all 3 piers, 6 local guides. Free, full text. |
| WORKS (expected ~Nov 1) | https://www.fishermanspost.com/topsail-sneads-ferry-november-2026/ | URL pattern is topsail-sneads-ferry-<month>-<year>. Not yet published on Oct 14; if 404, use the category index. |
| WORKS | https://www.fishermanspost.com/category/fishing-reports/wrightsville-beach/ | Monthly Wrightsville Beach reports (Johnnie Mercer's Pier, Intracoastal Angler, Wilmington guides). Neighbor-area context. |
| NO CURRENT CONTENT | https://www.thejollyroger.com/index.php?c=fishing | Jolly Roger Pier report page; last entry 6/1/25. |
| WORKS, no report | https://www.surfcityoceanpier.com/ | Pier hours/fees; "What's biting" points to Events tab. Live cams at /live-cams.html. |
| WORKS, no report | http://seaviewfishingpier.godaddysites.com/ (www.seaviewpier.com redirects here) | Seaview Pier info, fees at /pier-house. |
| NO CURRENT CONTENT | https://www.intracoastalangler.com/pages/fishing-report | Hampstead/Wilmington shop; latest report May 3, 2023. |
| WORKS, no report | https://www.eastcoastsports.com/ | Surf City shop hours/address only. Its staff report via Fisherman's Post. |
| WORKS, weak | https://captainexperiences.com/fishing-reports/locations/north-carolina/topsail-beach | Guide trip notes with RELATIVE dates only ("2 weeks ago"), mostly Wilmington boats. Use only with "per a guide report on Captain Experiences" and no date claims. |
| BLOCKED (403) | https://fishingbooker.com/reports/... | FishingBooker report pages and destination lists. |
| NO CURRENT CONTENT | https://www.carolinasportsman.com/fishing/ | Loads, but no Topsail reports (mostly SC/freshwater, record catches). The /fishing/fishing-reports/ path returned 404. |
| BLOCKED (empty page) | https://www.facebook.com/JollyRogerInnandPier ; https://www.facebook.com/SurfCityOceanPier | Facebook returns only the page title. Piers post daily catches here, but the routine cannot read them. |
| BLOCKED (empty page) | https://www.instagram.com/surfcityoceanpier/ | Instagram returns no post text. |
- Charter captains with their own written report pages: none found in the Topsail / Sneads Ferry / Hampstead area. Guides named in Fisherman's Post (Spring Tide, Speckled Specialist, Native Son, Plan 9, South End Adventures, Carolina Flats) surfaced only as booking listings. NO CURRENT CONTENT.

## Regulations and water closures (NCDMF)
| Status | URL | What it carries |
|---|---|---|
| WORKS | https://www.deq.nc.gov/current-fisheries-management-proclamations (pages ?page=0 to ?page=5) | All current proclamations, number, title, issue and effective dates, PDF links. Check page 0 (newest shellfish/flounder items appear there) for anything issued after Oct 14. |
| WORKS | https://www.deq.nc.gov/about/divisions/marine-fisheries/rules-proclamations-and-size-and-bag-limits/polluted-area-proclamations | Newest shellfish closures/reopenings (PA-xx-2026) with areas and effective times. Check daily for Topsail Sound and Stump Sound. |
| WORKS (HTML summary) | https://www.deq.nc.gov/about/divisions/marine-fisheries/rules-proclamations-and-size-and-bag-limits/recreational-size-and-bag-limits | Size/bag table "EFFECTIVE September 2, 2026". |
| WORKS (PDF saves to disk; read the saved file) | https://www.deq.nc.gov/printable-recreational-guide/open | 2-page 2026 guide, updated 9/2/2026. |
| PDFs: WORKS via the deq.nc.gov ".../open" links and most files.nc.gov links; the PDF is saved to disk and must be opened with a PDF reader step. One file (FF-31-2026) returned 403 from files.nc.gov. |
| WORKS | https://www.deq.nc.gov/news/press-releases | DEQ releases incl. Marine Fisheries and swimming advisories (sound-side sites). |
| Map (not text) | https://ncdenr.maps.arcgis.com/apps/webappviewer/index.html?id=5759aa19d7484a3b82a8e440fba643aa | Shellfish temporary-closure map; JavaScript, not readable by fetch. Use the polluted-area list instead. Phone hotline 252-515-5656. |
| Map (not text) | https://ncdenr.maps.arcgis.com/apps/dashboards/99430d6fd1824b78ae328c6a5538852f | Swimming advisory map; JavaScript. The list URL xapps.ncdenr.org/mf/beaches/notification.do returned 404. Use the DEQ press-releases page for advisories. |

## Weather, surf, tides, sun and moon
| Status | URL | What it carries |
|---|---|---|
| WORKS | https://forecast.weather.gov/MapClick.php?lat=34.3655&lon=-77.6294 | NWS point forecast, Topsail Beach (NWS Wilmington). 7-day text, hazards. |
| WORKS | https://forecast.weather.gov/product.php?site=ILM&issuedby=ILM&product=SRF | NWS Wilmington Surf Zone Forecast. Zone "Coastal Pender" (NCZ106) = Surf City and Topsail Beach: rip current risk, surf height, water temp, UV. |
| WORKS | https://forecast.weather.gov/product.php?site=MHX&issuedby=MHX&product=SRF | NWS Newport/Morehead City Surf Zone Forecast. Zone "Coastal Onslow" includes North Topsail Beach. |
| WORKS | https://forecast.weather.gov/shmrn.php?mz=amz250 | Marine forecast "Coastal waters from Surf City to Cape Fear NC out 20 nm": wind, seas, advisories. |
| WORKS | https://forecast.weather.gov/shmrn.php?mz=amz158 | Marine forecast "S of Cape Lookout to N of Surf City NC out 20 nm" (covers North Topsail / New River Inlet). |
| WORKS | https://www.ndbc.noaa.gov/station_page.php?station=41110 | Buoy 41110 Masonboro Inlet: live water temp, wave height/period (nearest wave buoy; ~25 mi SW of Topsail). |
| WORKS | https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions&application=topsail_reporter&begin_date=YYYYMMDD&end_date=YYYYMMDD&datum=MLLW&station=8657419&time_zone=lst_ldt&units=english&interval=hilo&format=json | NOAA hi/lo tide predictions. 8657419 = "Ocean City Beach (fishing pier)", North Topsail Beach, ocean side (34.4517, -77.495). Heights in feet above MLLW. |
| WORKS | same URL with station=8657813 | 8657813 = "Hampstead" (34.3394, -77.706), ICW/sound side across from Topsail Beach. |
| Other NOAA stations near the island | 8657167 New River Inlet; 8657002 Sneads Ferry, New River; 8658163 Wrightsville Beach. No NOAA station is named Topsail Beach, Surf City or New Topsail Inlet (NOAA station metadata API, 2026-10-14). |
| WORKS | https://aa.usno.navy.mil/api/rstt/oneday?date=YYYY-MM-DD&coords=34.37,-77.63&tz=-5&dst=true | US Naval Observatory sunrise/sunset/moonrise, moon phase and % illumination for Topsail Beach. |
| WORKS | https://aa.usno.navy.mil/api/moon/phases/date?date=2026-10-15&nump=4 | Moon phase dates (times in UT). |
| NO TEXT DATA | https://www.surfchex.com/cams/seaview-pier-north-topsail-beach/ | Cam page; text fields empty and cam "temporarily offline" on Oct 14. |
| REDIRECT to paywall service | https://www.swellinfo.com/surf-forecast/topsail-north-carolina | Redirects to tollbit.swellinfo.com; treat as BLOCKED. |
| WORKS | https://topsailguide.com/weather/ | Local site's surf/tide page (third-party; prefer NWS/NOAA). |

## Almanac for the window (precomputed 2026-10-14; still re-fetch daily)
Tides, NOAA predictions, feet above MLLW, local time (EDT through Oct 31, EST from Nov 1). Wind and pressure change real water levels.
Ocean side, 8657419 Ocean City Beach (North Topsail):
- Oct 29: L 3:33a -0.1 | H 10:16a 6.1 | L 4:46p 0.2 | H 10:36p 4.1
- Oct 30: L 4:27a 0.0 | H 11:12a 5.9 | L 5:44p 0.4 | H 11:35p 4.0
- Oct 31: L 5:27a 0.3 | H 12:13p 5.5 | L 6:47p 0.6
- Nov 1: H 12:42a 3.9 | L 5:35a 0.5 | H 12:20p 5.2 | L 6:52p 0.6
- Nov 2: H 12:55a 4.0 | L 6:50a 0.6 | H 1:27p 5.0 | L 7:55p 0.6
- Nov 3: H 2:06a 4.2 | L 8:06a 0.6 | H 2:32p 4.8 | L 8:52p 0.5
- Nov 4: H 3:10a 4.5 | L 9:16a 0.6 | H 3:31p 4.7 | L 9:42p 0.4
- Nov 5: H 4:06a 4.9 | L 10:17a 0.5 | H 4:24p 4.5 | L 10:27p 0.3
- Nov 6: H 4:55a 5.2 | L 11:10a 0.4 | H 5:11p 4.4 | L 11:09p 0.2
- Nov 7: H 5:39a 5.4 | L 11:58a 0.3 | H 5:55p 4.3 | L 11:47p 0.2
Sound side, 8657813 Hampstead (ICW):
- Oct 29: L 5:12a 0.1 | H 11:27a 4.7 | L 6:16p 0.5 | H 11:48p 3.4
- Oct 30: L 6:05a 0.2 | H 12:25p 4.6 | L 7:13p 0.6
- Oct 31: H 12:47a 3.4 | L 7:03a 0.3 | H 1:25p 4.5 | L 8:12p 0.7
- Nov 1: H 1:46a 3.4 | L 7:06a 0.4 | H 1:22p 4.3 | L 8:11p 0.7
- Nov 2: H 1:43a 3.5 | L 8:11a 0.4 | H 2:17p 4.2 | L 9:07p 0.6
- Nov 3: H 2:40a 3.6 | L 9:14a 0.5 | H 3:12p 4.0 | L 9:58p 0.5
- Nov 4: H 3:39a 3.8 | L 10:14a 0.5 | H 4:07p 3.9 | L 10:45p 0.4
- Nov 5: H 4:38a 3.9 | L 11:09a 0.5 | H 5:00p 3.8 | L 11:30p 0.3
- Nov 6: H 5:32a 4.1 | L 12:02p 0.6 | H 5:49p 3.6
- Nov 7: L 12:14a 0.3 | H 6:20a 4.2 | L 12:54p 0.6 | H 6:35p 3.6
Sun (USNO, Topsail Beach 34.37N 77.63W): Oct 29 rise 7:28a set 6:20p; Oct 30 7:29a/6:19p; Oct 31 7:30a/6:18p; Nov 1 6:31a/5:17p (EST); Nov 2 6:32a/5:16p; Nov 3 6:33a/5:15p; Nov 4 6:33a/5:14p; Nov 5 6:34a/5:13p; Nov 6 6:35a/5:13p; Nov 7 6:36a/5:12p.
Moon (USNO, times converted from UT): Full Moon Oct 26 (00:12 EDT); Last Quarter Nov 1 (20:28 UT = 3:28 PM EST); New Moon Nov 9 (07:02 UT = 2:02 AM EST). Illumination: Oct 29 83%, Oct 31 63%, Nov 1 52%, Nov 3 30%, Nov 5 13%, Nov 7 3%.
Note: Oct 29-30 morning highs (6.1 / 5.9 ft at the ocean station) are the biggest tides of the window; the Topsail Beach 2026 king-tide list was not checked (calendar.md).

## Local news and notices
| Status | URL | What it carries |
|---|---|---|
| WORKS | https://topsailbeachnc.gov/ (NO www) | Town of Topsail Beach home: notices, events list. www.topsailbeachnc.gov returns 404, confirmed. |
| WORKS | https://topsailbeachnc.gov/About-Topsail-Beach/News | Dated town news (south end, nature preserve, traffic, police). |
| WORKS | https://topsailbeachnc.gov/About-Topsail-Beach/Events | Town meeting/event calendar (link from home page). Not separately tested; home page already lists upcoming events. |
| WORKS | https://www.surfcitync.gov/ ; news https://www.surfcitync.gov/CivicAlerts.aspx?CID=1 ; calendar https://www.surfcitync.gov/calendar.aspx?CID=40,41,38,43,14,39 | Town of Surf City. Calendar showed October only. |
| WORKS | https://www.northtopsailbeachnc.gov/ ; news https://www.northtopsailbeachnc.gov/CivicAlerts.aspx?CID=1 | Town of North Topsail Beach; news list is detailed and dated. Calendar (/calendar.aspx?CID=22,23) showed no October events. |
| WORKS | https://www.pendercountync.gov/CivicAlerts.aspx?CID=1 | Pender County news (emergency, roads, elections). |
| WORKS | https://www.wect.com/news/ | WECT Wilmington: dated headlines; Pender items appear, Topsail items rare. |
| WORKS | https://www.wwaytv3.com/ | WWAY: relative timestamps; long page (use offset to read on). |
| WORKS | https://portcitydaily.com/ ; events https://portcitydaily.com/community-and-events/ | Port City Daily: dated headlines; weekly event roundups (e.g., Halloween list Oct 13, 2026). |
| WORKS | https://coastalreview.org/ | Coastal Review: NC coast/fisheries news, dated. |
| WORKS | https://topsailguide.com/ ; events https://topsailguide.com/events/ | Topsail Guide: local news, community event listings (neighbor-submitted; verify), directory. |
| WORKS | https://business.topsailchamber.org/event-calendar | Greater Topsail Area Chamber calendar (current month grid + upcoming list). |
| WORKS | https://www.visitpender.com/events | Pender County tourism events (showed Oct 15-Nov 26). |
| WORKS | https://www.onlyinonslow.com/events/ | Onslow County tourism events (Jacksonville, Sneads Ferry); 2 pages. |
| WORKS | https://topsailhistoricalsociety.org/ | Historical Society / Missiles and More Museum events. |
| WORKS | https://www.seaturtlehospital.org/visit/ | Sea turtle hospital tour dates (no public tours in October 2026). |
| BLOCKED (403) | http://www.postvoiceonline.com/ (www.post-voice.com redirects here) | Pender-Topsail Post & Voice. |
| BLOCKED (tool refuses) | https://www.starnewsonline.com/ | Wilmington StarNews. |
| BLOCKED (tool refuses) | https://www.jdnews.com/ | Jacksonville Daily News. |
| NO TEXT DATA | https://drivenc.gov/ and https://drivenc.gov/list/events/traffic | NCDOT traffic map/list loads by JavaScript; no rows come through. Use town/county news and WECT/WWAY for road closures. |
| WORKS | https://ncwildlife.gov/connect/ncwrc-operations-closings-and-alerts/boating-access-area-full-and-partial-closings | NCWRC boat ramp closures (no Pender/Onslow closures on Oct 14; page modified 10/12/2026). |
| NOT TESTED | https://www.wilmingtonandbeaches.com/events/ | Landing page only, no listings (NO CURRENT CONTENT). |

## Suggested morning fetch order
1. NWS point forecast + both Surf Zone Forecasts + AMZ250 marine + buoy 41110.
2. NOAA tide API (8657419 ocean, 8657813 sound) and USNO sun/moon for the day.
3. NCDMF polluted-area list (shellfish open/closed) and current-proclamations page 0 (any new rule).
4. Fisherman's Post Topsail category (new monthly report from ~Nov 1).
5. Town news: topsailbeachnc.gov (no www), surfcitync.gov, northtopsailbeachnc.gov; Pender County news.
6. WECT, WWAY, Port City Daily, Coastal Review headlines; Topsail Chamber and visitpender event lists.
