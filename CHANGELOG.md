# v0.4.2 (Thu Nov 07 2024)

#### 🚀 Enhancements

- [FIX] Filter for only `ImagingSession`s or `PhenotypicSession`s in SPARQL query [#375](https://github.com/neurobagel/api/pull/375) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.4.1 (Tue Oct 29 2024)

#### 🐛 Bug Fixes

- [FIX] Ensure non-agg API doesn't error out when all matches lack pipeline data [#369](https://github.com/neurobagel/api/pull/369) ([@alyssadai](https://github.com/alyssadai))

####  🧪 Tests

- [TST] Remove unneeded env file mount from test docker-compose.yml [#366](https://github.com/neurobagel/api/pull/366) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.4.0 (Thu Oct 24 2024)

#### 💥 Breaking Changes

- [REF] Split generic `/attributes` endpoints into attribute-specific routers [#358](https://github.com/neurobagel/api/pull/358) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Implemented `pipeline_version` and `pipeline_name` query fields [#345](https://github.com/neurobagel/api/pull/345) ([@rmanaem](https://github.com/rmanaem))

#### 🚀 Enhancements

- [ENH] Add `/pipelines` router & route for fetching available pipeline versions [#350](https://github.com/neurobagel/api/pull/350) ([@alyssadai](https://github.com/alyssadai))
- [REF] Update README links and simplify Docker Compose instructions [#340](https://github.com/neurobagel/api/pull/340) ([@alyssadai](https://github.com/alyssadai))

#### 🐛 Bug Fixes

- [FIX] Allow only `"true"` or `None` for `is_control` query parameter [#364](https://github.com/neurobagel/api/pull/364) ([@alyssadai](https://github.com/alyssadai))
- [FIX] Fixed a typo in filtering pipeline name [#351](https://github.com/neurobagel/api/pull/351) ([@rmanaem](https://github.com/rmanaem))
- [FIX] Ensure pipeline variables are returned from the graph in an aggregate query [#349](https://github.com/neurobagel/api/pull/349) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [MNT] Updated `default_neurobagel_query` [#347](https://github.com/neurobagel/api/pull/347) ([@rmanaem](https://github.com/rmanaem))
- [MNT] Removed build docker nightly workflow file [#342](https://github.com/neurobagel/api/pull/342) ([@rmanaem](https://github.com/rmanaem))

#### 📝 Documentation

- [MNT] Update default Neurobagel SPARQL query file and turn into PR checkbox [#359](https://github.com/neurobagel/api/pull/359) ([@alyssadai](https://github.com/alyssadai))

####  🧪 Tests

- [TST] Add integration test against local test graph [#357](https://github.com/neurobagel/api/pull/357) ([@rmanaem](https://github.com/rmanaem) [@surchs](https://github.com/surchs) [@alyssadai](https://github.com/alyssadai))

#### Authors: 3

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.3.1 (Tue Aug 13 2024)

#### 🐛 Bug Fixes

- [FIX] Ensure subjects without imaging sessions are considered in main query [#333](https://github.com/neurobagel/api/pull/333) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [CI] Fix reference for `DOCKERHUB_REPO` in build_docker_on_release.yml [#337](https://github.com/neurobagel/api/pull/337) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.1 (Tue Aug 13 2024)

#### 🐛 Bug Fixes

- [FIX] Ensure subjects without imaging sessions are considered in main query [#333](https://github.com/neurobagel/api/pull/333) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [CI] Release the node API [#336](https://github.com/neurobagel/api/pull/336) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.1 (Tue Aug 13 2024)

#### 🐛 Bug Fixes

- [FIX] Ensure subjects without imaging sessions are considered in main query [#333](https://github.com/neurobagel/api/pull/333) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.0 (Fri Aug 02 2024)

#### 💥 Breaking Changes

- [FIX] Disable redirect slashes globally and remove trailing `/` from `/query` [#328](https://github.com/neurobagel/api/pull/328) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Add authentication to `/query` route [#323](https://github.com/neurobagel/api/pull/323) ([@alyssadai](https://github.com/alyssadai))

#### 🐛 Bug Fixes

- [FIX] Exclude sessions missing a queried property from matches [#326](https://github.com/neurobagel/api/pull/326) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.2.1 (Tue Apr 16 2024)

#### 🐛 Bug Fixes

- [FIX] Address performance issues in SPARQL query [#308](https://github.com/neurobagel/api/pull/308) ([@surchs](https://github.com/surchs))
- [FIX] Disable timeout for request to graph [#305](https://github.com/neurobagel/api/pull/305) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.2.0 (Thu Apr 11 2024)

:tada: This release contains work from a new contributor! :tada:

Thank you, Abdul Samad Siddiqui ([@samadpls](https://github.com/samadpls)), for all your work!

### Release Notes

#### [MNT] Release new data model ([#300](https://github.com/neurobagel/api/pull/300))

We have updated the Neurobagel data model to allow users to specify phenotypic information at the session level (https://github.com/neurobagel/planning/issues/83). This release updates the node API so it can understand the new graph data.

---

#### 💥 Breaking Changes

- [REF] Make session count names clearer in query response [#282](https://github.com/neurobagel/api/pull/282) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Support queries of session-level phenotypic attributes [#264](https://github.com/neurobagel/api/pull/264) ([@alyssadai](https://github.com/alyssadai))

#### 🚀 Enhancements

- [ENH] Added root endpoint with welcome message and API docs link [#286](https://github.com/neurobagel/api/pull/286) ([@samadpls](https://github.com/samadpls))
- [MNT] Release new data model [#300](https://github.com/neurobagel/api/pull/300) ([@surchs](https://github.com/surchs))
- Delete .github/workflows/add_pr2project.yml [#244](https://github.com/neurobagel/api/pull/244) ([@surchs](https://github.com/surchs))

#### 📝 Documentation

- [DOC] Added warning about quoting in `.env` file for Docker commands [#284](https://github.com/neurobagel/api/pull/284) ([@samadpls](https://github.com/samadpls))
- [DOC] Add sample default SPARQL query to repo [#277](https://github.com/neurobagel/api/pull/277) ([@alyssadai](https://github.com/alyssadai))

####  🧪 Tests

- [TST] Refactor tests [#269](https://github.com/neurobagel/api/pull/269) ([@alyssadai](https://github.com/alyssadai))

#### 🔩 Dependency Updates

- Bumped fastapi, starlette, and typing_extensions [#295](https://github.com/neurobagel/api/pull/295) ([@rmanaem](https://github.com/rmanaem))

#### Authors: 4

- Abdul Samad Siddiqui ([@samadpls](https://github.com/samadpls))
- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))
- Sebastian Urchs ([@surchs](https://github.com/surchs))
