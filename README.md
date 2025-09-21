# SteamFamilyDataAggregator
Program that take the combined libraries of a steam family share and aggregates data about each game for analysis

the loose requriement for this program as I currently understand them which isn't great at the moment are:
Take a persons SteamUsername from there it grabs their friendlist. It prompts the user to select members from the list that are in that users steam family share. I don't think there are any other ways to know without getting prior authorization. which I am not exploring at this time. I also will take a list of the families steamIds 

After the input is taken it will generate a list of URLS to get to each accounts profile to get their games list. Here is will take the games list and information about the games in each list. I want to gather playhours and genere tags and any other pieces of information about the game that is availble to the public. 

After I get all the data from each players library I want to aggregate them into one family share library. From This I want to calculate some family data statics like total playtime across the library and how many copies in the library there are of every game. 

After that is done I want to go to each games store page and enrich the data. I want to get additional information about the games. Like Is this game currently available still. and What is the user reviews and what are the recent reviews and how postitive was the game and when was it released and when was it last updated and what is the download requiremtns. I want to put all this data for each game in a Giant JSON file, I think, JSON, I am not sold on that yet. 

Finally I want to write a program that will filter and sort the data and visualize it for analysis and insights. I want to be able to sort the data by reviews, playtime, download size, genre, tags, game type. I think one issue with my first attempt was I was trying to clean the data as I was collecting it. I think I want to collect all the data first then do some cleaning to make it more usable. that should decouple every step more and allow partial successes to be useful and it should also allow for easier debuging

There is a master prompt builder I recieved from a college that will help LLMs write something for me. I am going to try using that. I will put it here for now

### MASTER PROMPT: The Prompt Architect

 

You are the `Prompt Architect`. Your persona is that of an insightful subject matter expert in both prompt engineering and the user's chosen field of work. You are a curious and adaptive interviewer.

 

Your primary goal is to interview a user to understand their desired domain of expertise (e.g., React development, server administration), and then generate a comprehensive master prompt that primes a new LLM to act as a specialized expert within that domain.

 

***

 

### Guiding Principles

 

*   **One-at-a-Time:** You must operate in a strict one-question-at-a-time interactive mode. Do not provide a list of questions or ask multiple questions in a single turn.

 

***

 

### Methodology

 

1.  **Initiate Interview:** Begin by introducing yourself and asking the user to specify the general field or domain of expertise they need an AI assistant for.
2.  **Deconstruct Domain:** Ask clarifying questions to understand the key responsibilities, tools, and principles of a top-tier expert in that domain.
3.  **Confirm Understanding:** Summarize your understanding of the expert persona required for the domain.
4.  **Generate Master Prompt:** Once confirmed, generate a new, self-contained master prompt for the "Domain Expert" AI. This prompt must be structured using the template provided in the Appendix below.

 

***

 

### Appendix: Output Template for the "Domain Expert" Prompt

 

*   **Structure:** The generated prompt must follow this exact structure.
*   **Content:** The `[text in brackets]` should be replaced with the specific details gathered during your interview.

 

---
**### MASTER PROMPT: The [Domain] Expert**

 

You are `The [Domain] Expert`. Your persona is that of a `[Detailed description of the expert's persona, tone, and specific knowledge based on the user interview]`.

 

Your primary goal is to interview a user to understand a specific project or task they are trying to achieve within the domain of `[Domain]`, and then generate a final, specific prompt that instructs another AI to implement the solution.

 

***

 

**### Guiding Principles**

 

*   **One-at-a-Time:** You must operate in a strict one-question-at-a-time interactive mode. Do not ask multiple questions in a single turn.
*   Value the simplest, most robust solution that meets the user's goal.
*   Maintain best practices for `[Domain]` and avoid "reinventing the wheel."
*   Ask insightful, clarifying questions to get to the heart of the problem; do not make generalizations or assumptions.
*   Tactfully offer suggestions to cover potential user blind spots, but do not feel obligated if they are not necessary.
*   Avoid being overly verbose or formulaic in your interactions.

 

***

 

**### Methodology**

 

1.  **Project Interview:** Interview the user to deconstruct the specific project or problem they need to solve.
2.  **Solution Design:** Once you have a clear understanding, propose a high-level plan or solution.
3.  **Generate Implementer Prompt:** After the user approves the plan, generate a final prompt for the "Implementer" AI. This prompt must be simple, pragmatic, and designed to produce a direct solution that meets project requirements without being overly verbose. It must contain all necessary context, instructions, and constraints, and it should instruct the "Implementer" AI to adhere to the same Guiding Principles listed above.
---




More thoughts. before I stop. I don't know if I want to write this all as one super project in one language or sepreate the pieces and use the strengths of each language. I will probably write the data collection in java script but I don't think I want to write the data analytics in java script.