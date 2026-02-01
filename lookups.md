# Tree and Wood identifier lookups

## Linking Trees to Wood

Wikidata as a [natural product of taxon (P1582)](https://www.wikidata.org/wiki/Property:P1582) which can be tied to the natural product being wood as identified by [instance of (P31)](https://www.wikidata.org/wiki/Property:P31) [type of wood (Q1493054)](https://www.wikidata.org/wiki/Q1493054].

```
SELECT ?wood ?woodLabel ?tree ?treeLabel WHERE {
  ?wood wdt:P31 wd:Q1493054;
        wdt:P1582 ?tree.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
}
```
[query](https://query.wikidata.org/#SELECT%20%3Fwood%20%3FwoodLabel%20%3Ftree%20%3FtreeLabel%20WHERE%20%7B%0A%20%20%3Fwood%20wdt%3AP31%20wd%3AQ1493054%3B%0A%20%20%20%20%20%20%20%20wdt%3AP1582%20%3Ftree.%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cmul%2Cen%22.%20%7D%0A%7D)

This includes `?tree` taxa that are not species, such as the genus [Pinus (Q12024)](https://www.wikidata.org/wiki/Q12024) so we can limit only to `?tree` entries that are marked as being species. We can also group the cases where there are multiple woods from one type of tree:

```
SELECT ?tree ?treeLabel (GROUP_CONCAT(?woodLabel; SEPARATOR=", ") AS ?woodLabels) WHERE {
  ?wood wdt:P31 wd:Q1493054;
        wdt:P1582 ?tree.
  ?tree wdt:P105 wd:Q7432.  # limit to species only
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    ?wood rdfs:label ?woodLabel.
    ?tree rdfs:label ?treeLabel.
  }
} GROUP BY ?tree ?treeLabel
```
[query](https://query.wikidata.org/#SELECT%20%3Ftree%20%3FtreeLabel%20%3Fwoods_count%20%3FwoodLabels%20WHERE%20%7B%0A%20%20%7B%0A%20%20%20%20SELECT%20%3Ftree%20%3FtreeLabel%20%28COUNT%28%3Fwood%29%20AS%20%3Fwoods_count%29%20%28GROUP_CONCAT%28%3FwoodLabel%3B%20SEPARATOR%3D%22%2C%20%22%29%20AS%20%3FwoodLabels%29%20WHERE%20%7B%0A%20%20%20%20%20%20%3Fwood%20wdt%3AP31%20wd%3AQ1493054%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20wdt%3AP1582%20%3Ftree.%0A%20%20%20%20%20%20%3Ftree%20wdt%3AP105%20wd%3AQ7432.%20%20%23%20limit%20to%20species%20only%0A%20%20%20%20%20%20SERVICE%20wikibase%3Alabel%20%7B%0A%20%20%20%20%20%20%20%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22%20.%0A%20%20%20%20%20%20%20%20%3Fwood%20rdfs%3Alabel%20%3FwoodLabel.%0A%20%20%20%20%20%20%20%20%3Ftree%20rdfs%3Alabel%20%3FtreeLabel.%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%20GROUP%20BY%20%3Ftree%20%3FtreeLabel%0A%20%20%7D%0A%20%20FILTER%20%28%3Fwoods_count%20%3E%201%29%0A%7D)

And then selecting only those case that have multiple wood types:

```
SELECT ?tree ?treeLabel ?woods_count ?woodLabels WHERE {
  {
    SELECT ?tree ?treeLabel (COUNT(?wood) AS ?woods_count) (GROUP_CONCAT(?woodLabel; SEPARATOR=", ") AS ?woodLabels) WHERE {
      ?wood wdt:P31 wd:Q1493054;
            wdt:P1582 ?tree.
      ?tree wdt:P105 wd:Q7432.  # limit to species only
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
        ?wood rdfs:label ?woodLabel.
        ?tree rdfs:label ?treeLabel.
      }
    } GROUP BY ?tree ?treeLabel
  }
  FILTER (?woods_count > 1)
} ORDER BY DESC(?woods_count)
```
[query](https://query.wikidata.org/#SELECT%20%3Ftree%20%3FtreeLabel%20%3Fwoods_count%20%3FwoodLabels%20WHERE%20%7B%0A%20%20%7B%0A%20%20%20%20SELECT%20%3Ftree%20%3FtreeLabel%20%28COUNT%28%3Fwood%29%20AS%20%3Fwoods_count%29%20%28GROUP_CONCAT%28%3FwoodLabel%3B%20SEPARATOR%3D%22%2C%20%22%29%20AS%20%3FwoodLabels%29%20WHERE%20%7B%0A%20%20%20%20%20%20%3Fwood%20wdt%3AP31%20wd%3AQ1493054%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20wdt%3AP1582%20%3Ftree.%0A%20%20%20%20%20%20%3Ftree%20wdt%3AP105%20wd%3AQ7432.%20%20%23%20limit%20to%20species%20only%0A%20%20%20%20%20%20SERVICE%20wikibase%3Alabel%20%7B%0A%20%20%20%20%20%20%20%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22%20.%0A%20%20%20%20%20%20%20%20%3Fwood%20rdfs%3Alabel%20%3FwoodLabel.%0A%20%20%20%20%20%20%20%20%3Ftree%20rdfs%3Alabel%20%3FtreeLabel.%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%20GROUP%20BY%20%3Ftree%20%3FtreeLabel%0A%20%20%7D%0A%20%20FILTER%20%28%3Fwoods_count%20%3E%201%29%0A%7D%20ORDER%20BY%20DESC%28%3Fwoods_count%29)


## Restricting to species

Wikidata includes entries for various taxonomic ranks such as geneus (see, e.g. [Jujube]()). Taxonomic data typically includes the [taxon rank (P105)](https://www.wikidata.org/wiki/Property:P105) where the value we are most interested in is [species (Q7432)](https://www.wikidata.org/wiki/Q7432). There are a great many taxonomic ranks defined which can been seen with:

```
SELECT ?rank ?rankLabel ?item_count WHERE {
  {
    SELECT DISTINCT ?rank (COUNT(?taxon) as ?item_count) WHERE {
      ?rank wdt:P31 wd:Q427626.
      ?taxon wdt:P105 ?rank.
    } GROUP BY ?rank ?rankLabel
  }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    ?rank rdfs:label ?rankLabel.
  }
} ORDER BY DESC(?item_count)
```
[query](https://query.wikidata.org/#SELECT%20%3Frank%20%3FrankLabel%20%3Fitem_count%20WHERE%20%7B%0A%20%20%7B%0A%20%20%20%20SELECT%20DISTINCT%20%3Frank%20%28COUNT%28%3Ftaxon%29%20as%20%3Fitem_count%29%20WHERE%20%7B%0A%20%20%20%20%20%20%3Frank%20wdt%3AP31%20wd%3AQ427626.%0A%20%20%20%20%20%20%3Ftaxon%20wdt%3AP105%20%3Frank.%0A%20%20%20%20%7D%20GROUP%20BY%20%3Frank%20%3FrankLabel%0A%20%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%0A%20%20%20%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22%20.%0A%20%20%20%20%3Frank%20rdfs%3Alabel%20%3FrankLabel.%0A%20%20%7D%0A%7D%20ORDER%20BY%20DESC%28%3Fitem_count%29)

As of 2026-02-01 there are 3251308 species entries, the next most use rank being genus with 280413.

## Cornell University's Woody Plants Database

https://www.wikidata.org/wiki/Property:P10793
