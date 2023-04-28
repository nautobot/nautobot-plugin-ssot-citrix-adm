# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## v0.1.0 (2023-04-28)
### Feature
* ✨ Pass Job as logger to CitrixAdmClient class so we can notify user of progress and errors. ([`38b4bff`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/38b4bffdbbea0c3b768413bfc3f9e9f110871663))
* ✨ Add functions to load_addresses in both ADM and Nautobot. ([`1ca0873`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/1ca08733bb6fb057de5d6b8616ca6626f23fa039))
* ✨ Add function to get ports, load in ADM and Nautobot, add fixtures and tests to validate ([`d88c8db`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/d88c8dbba591f377be966b09874384b2f6ca505d))
* ✨ Add method to parse version from string and include test validating ([`aa81aba`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/aa81abaa9839ddfbd7b4b489be16bd5f8757632b))
* ✨ Add function to get_devices, load functions, and tests with fixtures ([`1254c35`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/1254c358a00882ec398a5b84f78b5c15f5d70465))
* ✨ Add function to get sites from ADM, include fixture and test validating load func ([`df06f37`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/df06f3707213733c6d066577363900d4b661726d))
* ✨ Build out remaining DiffSync models, build initial CRUD funcs for Nautobot models. ([`42c6c58`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/42c6c588839622781c2444f295c15cff0d2234a4))
* ✨ Add function to create Citrix Manufacturer at database ready signal ([`7a977a5`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/7a977a5598e8c4c8613db39c22a9bb7d82ab3116))
* ✨ Add initial client for communicating with ADM/MAS. ([`94d775d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/94d775d44648f53b5e00374414b94a54c04b2407))

### Fix
* 🐛 Correct params value to not be a list ([`d6e2ef0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/d6e2ef0b3d6f5d092d80d4f4abe6a7e19ab70d41))
* 🐛 Correct login and request functions to return json and use proper nesting for sessionID ([`97d584f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/97d584f924d73bb95380bae4b3df6a142aa8eaec))
* 🐛 Update login to have session cookie added to headers. ([`c477fc8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/c477fc80005f5f168d33c407d8dbd40d5b3998ab))
* Update Jobs to have client passed to it ([`23b2d8c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/23b2d8c15f5acc636034fbc7b1c2071a1d60812f))

### Documentation
* 📝 Add docstrings to functions ([`7888928`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/788892893db91aabbcde43a9d8baf5028e24f471))
* 📝 Update docstrings for CitrixNitroClient ([`131c02f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/131c02fb831b170b243c976a92d577a059a0f173))
* 📝 Fix docstring for return ([`e32eca0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/e32eca049b3f85d61650de4887b2ee9a6125ee3c))
* 🏷️ Update type for client var and docstring ([`3b4c8e3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/3b4c8e3e8dde06f1d1c443a3bf743d42effe1d27))
