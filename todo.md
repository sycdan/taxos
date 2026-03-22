# To Do: Taxos Development

## Today's Task

we need to start doing full e2e browser test flows that ensure the ui works as expected when hooked up to the real backend

please suggest tools we could use

we want to bea be to write tests without a lot of boilerplate and put them in the (not created yet) ./test domain

for example

```
dev.test --flows backdated
# flows would be a boolean flag, backdated would be in the current arg list (*tests)
```

would run the tests matching "*backdated*" in ./test/flows

we would create a new tenant for each flow, so they have a clean slate

we would need helpers to make it easy to set up a testbed of data in a new tenant for the purposes of that specific test

we will run these tests from the devcontainer, so http://frontend and http://backend urls should work (needs to be tested)

we will move the existing backdated flow test from frontend to this higher level, since it really neesd the ui; the basic api integration tests can stay (we should remove the integration tests on the backend though, since they are probably duplicated by the FE ones -- but move any missing logic over)