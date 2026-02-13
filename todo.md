# To Do: Taxos Development

## Today's Task

we need to start tracking vendors. the goal being to allow faster receipt by way of typeahead matching to previously-used vendors. this will also give us the ability to deduplicate/consolidate vendors, in case of typos on data entry. (we should do that as a separate flow afterwards as teh would be specific suer input needed, not tackling now)

i think we need a taxos.vendor entity & repo, and we can create them when we add receipts. we can store data in data/vendors
