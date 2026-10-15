# game-on-tv

Live sports broadcasts on French TV for the next two weeks, for the Game On app.

A GitHub Action runs `build_tv.py` twice a day: it downloads the French TV guide from
[xmltvfr.fr](https://xmltvfr.fr) ([XML-TV-Fr](https://github.com/racacax/XML-TV-Fr)), keeps the sport
programmes of at least an hour on sports channels (Canal+, beIN SPORTS, RMC Sport, Ligue 1+, DAZN…)
and publishes them as `tv.json`.
