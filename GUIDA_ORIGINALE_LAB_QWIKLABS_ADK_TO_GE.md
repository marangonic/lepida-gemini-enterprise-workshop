# Add an ADK Agent to Gemini Enterprise (Qwiklabs Guide)

## Overview

In this lab you will add a custom agent to a Gemini Enterprise deployment.

To do so, you will download sample code of an [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) agent that features a BigQuery toolset that can analyze and add data to BigQuery. You will deploy this agent to Agent Runtime, create an OAuth client to allow a user to authorize the agent, and add it to a Gemini Enterprise deployment.

In this lab, you will be acting as an engineer at **Cymbal Pools**, a swimming pool installation company. You will use the agent to analyze past pool-installation requests and enter new requests.

If you aren't familiar with the basics of Agent Development Kit, you can learn more in the labs [Get started with Agent Development Kit (ADK)](https://explore.qwiklabs.com/catalog_lab/32017) and [Empower ADK agents with tools](https://explore.qwiklabs.com/catalog_lab/32018).

---

## Objectives

In this lab, you learn how to:
- Provide an Agent Development Kit (ADK) agent a BigQuery Toolset to query and update data.
- Deploy an ADK agent to Agent Runtime.
- Create an OAuth consent screen and web application OAuth Client.
- Deploy Gemini Enterprise.
- Add an agent to Gemini Enterprise.

---

## Setup and requirements

### Before you click the Start Lab button

Read these instructions. Labs are timed and you cannot pause them. The timer, which starts when you click **Start Lab**, shows how long Google Cloud resources are made available to you.

This hands-on lab lets you do the lab activities in a real cloud environment, not in a simulation or demo environment. It does so by giving you new, temporary credentials you use to sign in and access Google Cloud for the duration of the lab.

To complete this lab, you need:
- Access to a standard internet browser (Chrome browser recommended).

> [!NOTE]
> Use an Incognito (recommended) or private browser window to run this lab. This prevents conflicts between your personal account and the student account, which may cause extra charges incurred to your personal account.

- Time to complete the lab—remember, once you start, you cannot pause a lab.

> [!NOTE]
> Use only the student account for this lab. If you use a different Google Cloud account, you may incur charges to that account.

### How to start your lab and sign in to the Google Cloud console

1. Click the **Start Lab** button. If you need to pay for the lab, a dialog opens for you to select your payment method. On the right is the **Lab setup** pane with the following:
   - The **Open Google Cloud console** button
   - The temporary credentials that you must use for this lab
   - Other information, if needed, to step through this lab
2. In the **Lab Setup** section, right-click **Open Google Cloud console** and select **Open link in new window** (or alternatively right-click and select **Open Link in Incognito Window** if you are running the Chrome browser).
   The lab spins up resources, and then opens another tab that shows the **Sign in** page.
   - **Tip:** Arrange the tabs in separate windows, side-by-side.
   - **Note:** If you see the **Choose an account** dialog, click **Use Another Account**.
3. If necessary, copy the **Username** below and paste it into the **Sign in** dialog. You can also find the Username in the **Lab Setup** pane.
4. Click **Next**.
5. Copy the **Password** below and paste it into the **Welcome** dialog. You can also find the Password in the **Lab Setup** pane.
6. Click **Next**.

> [!IMPORTANT]
> You must use the credentials the lab provides you. Do not use your Google Cloud account credentials. Using your own Google Cloud account for this lab may incur extra charges.

7. Click through the subsequent pages:
   - Accept the terms and conditions.
   - Do not add recovery options or two-factor authentication (because this is a temporary account).
   - Do not sign up for free trials.

After a few moments, the Google Cloud console opens in this tab.

> [!NOTE]
> To access Google Cloud products and services, click the **Navigation menu** or type the service or product name in the **Search** field.

---

## Task 1. Install ADK and set up your environment

In this task you'll set up Cloud Shell Terminal and Cloud Shell Editor to function as an IDE in Google Cloud. You'll then install Agent Development Kit (ADK) and download some sample code for the lab.

> [!NOTE]
> Using an Incognito browser window is recommended for most Qwiklabs to avoid confusion between your Qwiklabs student account and other accounts logged into Google Cloud. If you are using Chrome, the easiest way to accomplish this is to close any Incognito windows, then right click on the **Open Google Cloud console** button at the top of this lab and select **Open link in Incognito window**.

### Enable recommended Agent Platform APIs

In this lab environment, the Agent Platform API has been enabled for you. If you were to follow these steps in your own project, you could enable it by navigating to **Agent Platform** and following the prompt to enable it.

### Prepare a Cloud Shell Editor tab

1. Click **Activate Cloud Shell** in the Google Cloud console title bar.
   - *Note:* Alternatively, select the console browser tab and press `G` then `S` to open the Cloud Shell terminal.
2. Click **Continue**.
3. When prompted to authorize Cloud Shell, click **Authorize**.
4. In the upper right corner of the Cloud Shell Terminal panel, click the **Open in new window** button.
5. Click the **Open Editor** pencil icon at the top of the pane to view files.
6. At the top of the left-hand navigation menu, click the **Explorer** icon to open your file explorer.
7. Click the **Open Folder** button.
8. In the **Open Folder** dialog that opens, click **OK** to select your Qwiklab student account's home folder.
9. Close any additional tutorial or Gemini panels that appear on the right side of the screen to save more of your window for your code editor.

Throughout the rest of this lab, you can work in this window as your IDE with the Cloud Shell Editor and Cloud Shell Terminal.

### Install ADK and download code for this lab

1. Paste the following commands into the Cloud Shell Terminal to copy a file from a Cloud Storage bucket, creating a project directory with code for this lab:

```bash
gcloud storage cp -r gs://YOUR_GCP_PROJECT_ID-bucket/adk_to_ge .
```

2. Update your `PATH` environment variable and install project requirements including a version of ADK compatible with Agent Runtime by running the following commands in the Cloud Shell Terminal:

```bash
export PATH=$PATH:"/home/${USER}/.local/bin"
python3 -m pip install -r adk_to_ge/requirements.txt
gcloud config set project YOUR_GCP_PROJECT_ID
```

3. Write a `.env` file to provide authentication details for this agent directory by running the following in the Cloud Shell Terminal:

```bash
cd ~/adk_to_ge
cat << EOF > bigquery_agent/.env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
MODEL=gemini-3.5-flash
EOF
```

---

## Task 2. Deploy an Agent to Agent Runtime

In this task you'll review the agent you'll use for the lab and deploy it to Agent Runtime.

1. In your Cloud Shell Editor, browse to the folder `adk_to_ge/bigquery_agent` and open the file `agent.py`.
   Notice a few things in this file:
   - `BigQueryToolset` and a few config classes are imported from `google.adk.tools.bigquery`.
   - When that toolset is instantiated, it is configured with a `BigQueryCredentialsConfig` that uses Application Default Credentials and a `BigQueryToolConfig` that grants this tool permission to write data in addition to reading it.
   - In addition to the `BigQueryToolset` tool, the agent is given a `get_current_time` function to be aware of the current time.

2. Deploy the agent to Agent Runtime by running the following command:

```bash
adk deploy agent_engine \
  --display_name "BigQuery Pool Data Agent" \
  --project PROJECT_ID \
  --region REGION \
  --staging_bucket gs://Project_ID-bucket \
  bigquery_agent
```

This should take about 5–10 minutes. While the agent is deploying, you can proceed with the next task.

Expected output ends with:

```text
Initializing Vertex AI...
Vertex AI initialized.
Created bigquery_agent_tmp20260918_111808/agent_engine_app.py
Files and dependencies resolved
Deploying to agent engine...
✅ Created agent engine: projects/431512375425/locations/us-central1/reasoningEngines/1887575042112356352
🎉 View your deployed agent here: https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/1887575042112356352/playground?project=431512375425
Cleaning up the temp folder: bigquery_agent_tmp20260918_111808
```

---

## Task 3. Set up an OAuth Consent Screen and Client

In order for the AI assistant to take actions on a user's behalf, the user must be able to authorize the agent to do so. You'll make that possible by configuring an OAuth consent screen and client in this task.

1. Return to your browser tab displaying the Cloud Console (the tab you used to launch your Cloud Shell & Cloud Editor tab) and close the Cloud Shell Terminal panel at the bottom of that tab.
2. Use the search bar at the top of the Cloud Console to search for the **Google Auth Platform** and select it.
3. Click **Get started**.
4. For **App Name**, enter `Cymbal Pools Auth`.
5. For the **User support email**, select your Qwiklabs student account `Username`.
6. Click **Next**.
7. In the **Audience** section, select an **Internal** Audience.
8. Click **Next**.
9. In the **Contact Information** section, provide your Qwiklabs student account again: `Username`. Click **Next**.
10. In the **Finish** section, agree to the terms.
11. Click **Create** to create your OAuth consent screen.
12. Your Google Auth Platform dashboard will display a banner that you haven't created any clients yet. Select **Create OAuth Client**. If you don't see this banner, select **Clients** on the left and then **+ Create Client**.
13. Select an **Application type** of **Web application**.
14. Name the client `Gemini Enterprise Client`.
15. Under **Authorized redirect URIs**, add the following as specified [in the documentation](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent#obtain_authorization_details):
    - `https://vertexaisearch.cloud.google.com/oauth-redirect`
    - `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`
16. Click **Create**.
17. Once the OAuth client is created, a popup will display the client information. You will need to get the **Client ID** and **Client Secret** for this client and copy them to a note for use later. You may be able to download a JSON that includes these values from the pop-up after creation, or you might need to dismiss the pop-up and click on the client name. When viewing the client details, your window may need to be wide to see these values on the right.

> [!NOTE]
> If you were unable to save the client secret when the OAuth client was created, you can generate a new one by clicking **Add secret**. After the new client secret is created, download and save it securely. Once you have confirmed that the new secret is working, you can disable and delete the old client secret.

18. Click **Check my progress** to verify the objective: *Set up an OAuth Consent Screen and Client*.

---

## Task 4. Deploy Gemini Enterprise

In this task you will deploy a Gemini Enterprise app to act as a central pane of glass for agents you deploy.

1. On the browser tab displaying the Google Cloud Console, use the search bar at the top of the console to navigate to **Gemini Enterprise**.
2. Click **Create your first app**. If asked to do so, enable the API.
3. Name your app `Cymbal Pools GE`.
4. Under **Choose a location**, select `global (Global)` from the **Multi-region** drop-down menu.
5. Under **Advanced Options**, for a company name, enter `Cymbal Pools`.
6. Click **Create**.
7. Click **Check my progress** to verify the objective: *Deploy Gemini Enterprise*.

---

## Task 5. Add the ADK Agent to Gemini Enterprise

In this task, you add the agent you deployed to Agent Runtime to your Gemini Enterprise app.

### Add an authorization to Gemini Enterprise

1. After creating the Gemini Enterprise app, you should be on your app's **Overview** menu.
2. Click **Agents** on the left.
3. Click **+ Add agent**.
4. On the card labeled **Custom agent via Agent Runtime**, select **Add**.
5. Click **Add authorization**.
6. For an **Authorization name**, enter `BigQuery Agent Auth`.
7. For **Client ID**, enter the Client ID of the OAuth web application client you created earlier.
8. For **Client secret**, enter the matching Client Secret.
9. For **Token URI**, enter the Token URI which would have been included in the client JSON. It will be:

```text
https://oauth2.googleapis.com/token
```

10. For **Authorization URI**, you must construct a URL beginning with `https://accounts.google.com/o/oauth2/v2/auth` that includes URL-encoded query parameters for the `redirect_uri`, `scope`, `include_granted_scopes`, `response_type`, `access_type`, and `prompt`.
    - A script has been provided to help you construct this URL. Return to the Cloud Shell Editor and navigate to the file `adk_to_ge/construct_auth_uri.py`.
    - In this file, replace `YOUR_CLIENT_ID` with the Client ID of the OAuth web application client.
    - Define the list of `SCOPES` to include the BigQuery API that your agent will use:

```python
SCOPES = ['https://www.googleapis.com/auth/bigquery']
```

11. In the Cloud Shell Terminal, run the script to assemble the query parameters and HTML-encode them (replacing characters like `:` with `%3A` and `/` with `%2F`), printing the final URL:

```bash
cd ~/adk_to_ge
python3 construct_auth_uri.py
```

*(If you would like to save this script to construct authorization URIs in the future, you can download it from Cloud Shell Editor.)*

12. Copy the URL printed to the Cloud Shell Terminal, which should look like the following (but include your Client ID), return to the Gemini Enterprise tab where you are adding the agent authorization, and paste it into the Agent's **Authorization URI** field:

```text
https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fbigquery&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent
```

13. Click **Done**.
14. Click **Next**.
15. For an **Agent name**, enter `BigQuery Agent`.
16. For an **Agent description**, enter `Queries BigQuery data to assist with pool installation requests.`
17. Return to the Cloud Shell Terminal browser tab and find the output line that looks like this:

```python
agent_engine = vertexai.agent_engines.get('projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/reasoningEngines/YOUR_REASONING_ENGINE_ID')
```

*(You could also locate this resource name by navigating to Agent Runtime in the Console. Alternatively, go to **Agent Platform > Agents > Deployments**.)*

18. Copy the string within the `get()` method, from `projects/` through the ending Reasoning Engine ID number and use it as the value for **Agent Engine reasoning engine**.
19. Click **Create**.

### Grant user permissions to be able to use the agent

1. In the Gemini Enterprise console, navigate to **Agents** and then click your agent named **BigQuery Agent**. If it isn't yet listed, refresh the page.
2. Click the **User permissions** tab.
3. Click **Add user**.
4. Select **All users**.
5. Select the role of **Agent User**.
6. Click **Save**.

### Grant the agent required roles for its tools

1. To grant your deployed agent the access it needs to use its `BigQueryToolset`, navigate to **IAM & Admin**.
2. Click the checkbox to **Include Google-provided role grants**.
3. Find the **AI Platform Reasoning Engine Service Agent** and click the pencil icon to edit its roles.
4. Grant it the **BigQuery User** and **BigQuery Data Editor** roles and click **Save**.
5. Click **Check my progress** to verify the objective: *Add the ADK Agent to Gemini Enterprise*.

---

## Task 6. Communicate with your conversational agent through the Gemini Enterprise assistant

Now you'll see the benefits of your work by chatting with your agent, asking it to analyze existing data and add new data to a BigQuery table.

1. Return to your Gemini Enterprise console and click your deployed Gemini Enterprise app.
2. Click the **Integration** tab in the left-hand menu.
3. Select **Use Google Identity** to use Google as your identity provider.
4. Click **Confirm Workforce Identity**.
5. Click the visible URL or **Preview** link to open your Gemini Enterprise web app.
6. In the navigation bar on the left, click **Agents**, then on the Agents page, click **BigQuery Agent**. *(You can also use the three-dots menu to Pin it to the left-hand navigation menu.)*
7. Greet the agent with `hello`. The agent should let you know if it needs additional authorization.
8. Ask the agent:

```text
What is the schema of the installation_requests table?
```

9. Instruct the agent:

```text
Display the most recent 5 entries from the installation_requests table.
```

10. Instruct the agent:

```text
What is the average volume (length * width * depth) of pools we have been requested to install?
```

*(The agent should provide an answer. You can see the query that it ran to answer the question by navigating to **BigQuery > Explorer > Job history > Project history**.)*

11. Tell the agent:

```text
We received a new pool request. Please help me record it in the installation_requests table. What fields do you need?
```

*(The agent should reply with the schema that needs to be recorded for a new entry.)*

12. Reply with:

```text
The dimensions are 20m in length, 10m in width, and 3m in depth. It will include a hot tub but not a waterfall. It will be installed in zipcode 70124. Customer phone is 504.555.7414 and the email address is pool-dad@qwiklabs.net. It was requested today.
```

13. You can verify that the new record appears in the BigQuery table by asking:

```text
Display today's entry from the installation_requests table.
```
