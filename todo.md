# To Do: Taxos Development

## Today's Task

we would like to split the flow test files into smaller units inside each file, since they should run consecutively (so state from ealier tets can be sued in later ones, I assume). taht way we can more celarly see which unit of work failed.

we need to fix an issue with the backdated receipt test

there is some sort of race condition, where when we switch the filter to the backdate, the getdashboard call comes back and updates the view, then another getdashboad call compeletes (from saving the receipt, presumably) and it overrides the view

