## 🚀 **AI-Powered Database CRUD API & UI Generator**  
#### _Instantly generate full-stack admin panels, APIs, and UI from your database schema—powered by AI agents & LLMs_

**⚡ Automate 80% of your boilerplate code** – Say goodbye to manual CRUD coding! Let AI generate clean, production-ready database interfaces in seconds.  

- **✨ AI Agents** analyze your schema and generate optimized REST APIs  
- **🖥️ Auto-generated Admin UI** with filters, search, and CRUD operations  
- **🔌 Multi-DB Support** (SQL & NoSQL) with intelligent schema detection  
- **🎨 Customizable Templates** (React + MUI DataGrid)
- **🔒 Built-in Auth & Permissions** scaffolding  
- **📦 One-Codebase Export** for easy integration  

### 🚀 Perfect for:  
- Anyone wanting to quickly interact with their data for admin / internal purposes
- Devs tired of writing repetitive CRUD code  
- Teams managing complex data without dedicated frontend resources  
- AI engineers who want database UIs without full-stack work  

#### Supported Databases  
✅ MongoDB • ✅ PostgreSQL • 🔜 MySQL • 🔜 Redis • 🔜 Cassandra  ⚪ DynamoDB

---
![Revolve](https://raw.githubusercontent.com/self-evolving-runtimes/revolve/refs/heads/main/screenshots/animated.gif)

---
### Installation

Install the package from PyPI:

```sh
pip install selfrevolve
```

Run the API and UI:

```sh
revolve-api
```

For local development instructions, see [contributor-README.md](https://huggingface.co/kramster/evolve-mistral).


### Roadmap

- [ ] Authz and Authn configuration
- [ ] Support for other databases
- [ ] Support foreign key testing 
- [ ] Enhance UI to support lookups for foreign keys and editing json elegantly
- [X] Support for enums validation while editing via the discovery apis
- [X] Multi-turn conversations 
- [X] Fine-tuned model integration alongside support for the paid LLM APIs – see [kramster/evolve-mistral](https://huggingface.co/kramster/evolve-mistral) on Hugging Face for details.


### License

MIT
