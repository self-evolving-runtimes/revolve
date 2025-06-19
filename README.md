## 🚀 AI-Powered Database CRUD API & UI Generator  
#### _Instantly generate full-stack admin panels, APIs, and UI from your database schema—powered by AI agents & LLMs_

[![PyPI version](https://img.shields.io/pypi/v/selfrevolve.svg?color=blue)](https://pypi.org/project/selfrevolve/)
[![License](https://img.shields.io/github/license/self-evolving-runtimes/revolve)](https://github.com/self-evolving-runtimes/revolve/blob/main/LICENSE)
[![Model](https://img.shields.io/badge/model-Mixtral%20%F0%9F%94%93-brightgreen)](https://huggingface.co/kramster/evolve-mistral)
[![Open Source](https://img.shields.io/badge/open--source-yes-brightgreen)](https://github.com/self-evolving-runtimes/revolve)

---

**⚡ Automate 80% of your boilerplate code** – Say goodbye to manual CRUD coding! Let AI generate clean, production-ready database interfaces in seconds.

- **✨ AI Agents** analyze your schema and generate optimized REST APIs  
- **🖥️ Auto-generated Admin UI** with filters, search, and CRUD operations  
- **🔌 Multi-DB Support** (SQL & NoSQL) with intelligent schema detection  
- **🎨 Customizable Templates** (React + MUI DataGrid)  
- **📦 One-Codebase Export** for easy integration  

---

### 🧠 New: Open-Source Model Support (Mixtral)  
We now support a fine-tuned **Mixtral-based open model**, delivering performance **on par with GPT‑4.1** — tailored for Revolve use cases.

✅ Open weights, self-hostable  
✅ No OpenAI keys or API fees  
✅ Matches GPT‑4.1-level quality in schema-driven generation and agent workflows

Use it directly through the UI — just select the `mixtral-finetuned` model at runtime.  
🔗 [See the model on Hugging Face →](https://huggingface.co/kramster/evolve-mistral)

> Enterprise-grade quality without vendor lock-in.

---

### 🚀 Perfect for:
- Anyone wanting to quickly interact with their data for admin / internal purposes  
- Devs tired of writing repetitive CRUD code  
- Teams managing complex data without dedicated frontend resources  
- AI engineers who want database UIs without full-stack work  

#### Supported Databases  
✅ MongoDB • ✅ PostgreSQL • 🔜 MySQL • 🔜 Redis • 🔜 Cassandra ⚪ DynamoDB  

---
![Revolve](https://raw.githubusercontent.com/self-evolving-runtimes/revolve/refs/heads/main/screenshots/animated.gif)

---

### 📦 Installation

Install the package from PyPI:

```sh
pip install selfrevolve
```

Run the API and UI:

```sh
revolve-api
```

For local development instructions, see [contributor-README.md](https://huggingface.co/kramster/evolve-mistral).

---

### 🛣️ Roadmap

- [ ] Authz and Authn configuration  
- [ ] Support for other databases  
- [ ] Support foreign key testing  
- [ ] Enhance UI to support lookups for foreign keys and editing JSON elegantly  
- [X] Support for enums validation via the discovery APIs  
- [X] Multi-turn conversations  
- [X] Fine-tuned open-source model (Mixtral) support alongside paid LLM APIs  

---

### ⚖️ License

MIT
