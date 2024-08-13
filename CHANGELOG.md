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
