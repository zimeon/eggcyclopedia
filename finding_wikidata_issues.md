# Find relevant wikidata issues

## Natural product of taxon and its inverse

The property [natural product of taxon (P1582)](https://www.wikidata.org/wiki/Property:P1582) should usually be matched with inverse property [this taxon is source of (P1672](https://www.wikidata.org/wiki/Property:P1672) per <https://www.wikidata.org/wiki/Property_talk:P1582>.  

```
SELECT ?item ?itemLabel ?should_link_via_P1672_to ?should_link_via_P1672_toLabel
WHERE
{
	?should_link_via_P1672_to wdt:P1582 ?item .
	FILTER NOT EXISTS { ?item wdt:P1672 ?should_link_via_P1672_to } .
	SERVICE wikibase:label { bd:serviceParam wikibase:language "en,mul" } .
    # Limit only species and associate woods that they are products of
    ?item wdt:P105 wd:Q7432.  # limit to species only
    ?should_link_via_P1672_to wdt:P31 wd:Q1493054.  # wood
}
LIMIT 100
```
[query](https://query.wikidata.org/#SELECT%20%3Fitem%20%3FitemLabel%20%3Fshould_link_via_P1672_to%20%3Fshould_link_via_P1672_toLabel%0AWHERE%0A%7B%0A%09%3Fshould_link_via_P1672_to%20wdt%3AP1582%20%3Fitem%20.%0A%09FILTER%20NOT%20EXISTS%20%7B%20%3Fitem%20wdt%3AP1672%20%3Fshould_link_via_P1672_to%20%7D%20.%0A%09SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%2Cmul%22%20%7D%20.%0A%20%20%20%20%23%20Limit%20only%20species%20and%20associate%20woods%20that%20they%20are%20products%20of%0A%20%20%20%20%3Fitem%20wdt%3AP105%20wd%3AQ7432.%20%20%23%20limit%20to%20species%20only%0A%20%20%20%20%3Fshould_link_via_P1672_to%20wdt%3AP31%20wd%3AQ1493054.%20%20%23%20wood%0A%7D%0ALIMIT%20100)

* 2026-02-01 Added missing link for Black Cherry `wd:Q158987 wdt:P1672 wd:Q119199156`

Swapped around we can also look for missing P1582 links per <https://www.wikidata.org/wiki/Property_talk:P1672>:

```
SELECT ?item ?itemLabel ?should_link_via_P1582_to ?should_link_via_P1582_toLabel
WHERE
{
	?should_link_via_P1582_to wdt:P1672 ?item .
	FILTER NOT EXISTS { ?item wdt:P1582 ?should_link_via_P1582_to } .
	SERVICE wikibase:label { bd:serviceParam wikibase:language "en,mul" } .
    # Limit only species and associated woods that they are products of
    ?should_link_via_P1582_to wdt:P105 wd:Q7432.  # limit to species only
    ?item wdt:P31 wd:Q1493054.  # wood
}
LIMIT 100
```
[query](https://query.wikidata.org/#SELECT%20%3Fitem%20%3FitemLabel%20%3Fshould_link_via_P1582_to%20%3Fshould_link_via_P1582_toLabel%0AWHERE%0A%7B%0A%09%3Fshould_link_via_P1582_to%20wdt%3AP1672%20%3Fitem%20.%0A%09FILTER%20NOT%20EXISTS%20%7B%20%3Fitem%20wdt%3AP1582%20%3Fshould_link_via_P1582_to%20%7D%20.%0A%09SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%2Cmul%22%20%7D%20.%0A%20%20%20%20%23%20Limit%20only%20species%20and%20associated%20woods%20that%20they%20are%20products%20of%0A%20%20%20%20%3Fshould_link_via_P1582_to%20wdt%3AP105%20wd%3AQ7432.%20%20%23%20limit%20to%20species%20only%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ1493054.%20%20%23%20wood%0A%7D%0ALIMIT%20100)
