# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## v1.0.0 (2023-05-04)
### Feature
* ✨ Add LabelMixin to add CustomField for SoR and Last Sync updates ([`8778924`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/87789246f16492d73e2d68a17b322e3391afc3bd))
* ✨ Add Platform for netscaler and ensure Devices are set to it at creation ([`efdb9ef`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/efdb9ef39ca596317dcfd2b0855070a1d6741079))
* 🎨 Update CRUD functions for all Nautobot models to use all model attributes. ([`993c89e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/993c89e5e2fd2e70f002c0b5a2ee4d84921a3dc4))
* ✨ Add primary attribute to Address object to know if primary for Device. ([`51cbbe6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/51cbbe6f0387130c83b696d1faf78e867a2fc795))
* ✨ Create Citrix Manufacturer and CustomFields after database ready signal ([`5ef9363`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/5ef9363d2dc26d4bd590a3069c904e3eca2fa165))

### Fix
* 🐛 Remove unused import ([`179bcce`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/179bcce1443c6ad17c4ecb94d2a920e56a97d14b))
* 🐛 Correct attribute to be port ([`e183899`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/e183899f3ac179f79670720dfbaff1070ee96483))
* 🐛 Add LabelMixin as parent inherited class for CustomFields to CitrixAdmAdapter ([`ef57861`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/ef578617908f4622cf3fd1b5b6823341f45b9cc2))
* 🐛 Correct attributes for load_address to be assigned_object ([`5119f31`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/5119f31d49365bad7dd45a9a403bd987c5af1a94))
* 🐛 Ensure latitude/longitude strips trailing zeroes for diff ([`d868c9a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/d868c9ab934f4c4f8c67aa02f7449b4eb4ae9fbe))
* 🐛 Fix attribute to device_role, ensure update function is correct and has all attributes ([`244e653`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/244e6534621c9c8686b2b9266b686a16e0aedbe4))
* 🐛 Helps to put a continue when skipping! ([`a6f0ad8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/a6f0ad864f0ea0471dbe02c28fedc667f81b0f58))
* 🐛 Ensure signals are called after database ready, update test ([`c90202c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/c90202ce4ad836963f3afd8feb76b06dfaf01b01))
* 🐛 Correct attribute to serial ([`0aa9f5c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/0aa9f5ca9023d8d546ee8508b7fee23463246f39))
* 🐛 Correct get_or_create response is a tuple! ([`5e883a6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/5e883a61c4d9165d354fb18afd97f3612ec43698))
* 🐛 Ensure that region is same as ADM so that diff lines up ([`c9dc34d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/c9dc34df845ff778884fad9bfa27337a69cb5fdb))
* 🐛 Correct status to be Active instead of attr, use get_or_create for Region ([`24156d3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/24156d39403ef31190cebece35b41d99a1ad7231))
* 🐛 Skip loading of Default datacenter from ADM. ([`06c0760`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/06c0760c03e95aeafd85a397f162e62be2a7483a))
* 🐛 Ensure type and mgmt_only are set on newly created Interfaces. ([`0b81666`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/0b81666aacf3f83ed7d2214bd356b26c2ed3e19a))
* 🐛 Fix logout functionality by adding payload with logout and credentials to match login ([`071cc2a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/071cc2a02641482e95044bd5793f25a3fc302f1a))
* 🐛 Ensure Management port is added to device so it's processed too! ([`f3f44be`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/f3f44be3c8df218b7416490c1e90dd980c08c9a1))
* 🐛 Ignore devices without a hostname. ([`a5697fe`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/a5697fe61c13b9a78770fcd4661c96ec305cb640))
* 🐛 Remove port from top_level so they aren't processed twice ([`7caaa1e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/7caaa1e75a676808590f3c236162f3ff33ac5989))
* 🐛 Helps to do the login and logout! ([`8688cc3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/8688cc3bd6dfd30bae0f9f15b994a59b73d35072))
* 🐛 Correct login to use Cookie, not Set-Cookie for header key ([`085c5bc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/085c5bcc4461b2973288f7911897b21ea9cf7d97))

### Documentation
* ⏪️ Redo docstring correction that shouldn't have been reverted in previous commit ([`0afd93f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/0afd93f5780caa661b41ed54451141196bc0e3b2))
* 📝 Correct docstring ([`da8818c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-citrix-adm/commit/da8818c431802f0a16b3783bd8cfbc0471747615))

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
