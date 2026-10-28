# Infrastructure as Code with AWS CDK: A Hands-On Guide for AWS Beginners

This guide is for engineers who are new to AWS and want to learn how real teams set up cloud infrastructure. We'll start with how the industry got here, then build a small app step by step with **AWS CDK**, explaining what happens under the hood and answering the questions beginners usually have along the way.

## Background: how teams set up cloud resources

Every app on AWS needs **infrastructure**: the storage, databases, servers, networks and permissions it runs on. Over the years, engineers have created that infrastructure in three main ways. Each one was invented to fix the problems of the one before it.

To make this concrete, follow one small team through all three. You've just joined **Crumb & Co.**, a local bakery that takes custom cake orders online. The owner wants a new feature: customers upload a photo of the cake they have in mind, and the bakers see a list of every photo, with its name, size and upload time.

### Era 1: clicking in the console

Most people meet AWS through the **AWS Management Console**, the website where you click "Create bucket", fill in a form and press a button. Engineers jokingly call running infrastructure this way **"ClickOps"**.

On Friday you click the feature together: a storage bucket for the photos, a database table for the list, and a small function that connects them. It works, and you go home happy.

On Monday the owner says: *"Before the holiday rush, let's have a separate test copy, so we don't break the live site."* You try to repeat about forty clicks from memory. You miss one setting: the test function times out after 3 seconds instead of 30. Now big photos work in production but fail in testing, and you lose an afternoon working out why the two copies behave differently.

That's the core problem with clicking: **the console doesn't remember *why* things are the way they are, and you can't replay it.** A setup made by hand can't be reviewed, copied exactly, or rebuilt after a mistake. It lives only in someone's memory or, at best, in a wiki page of screenshots that slowly goes out of date.

### Era 2: scripts that create resources one by one

The natural next step, and how many teams worked for years: **write code that makes the same API calls the console makes.** You can do this with shell scripts using the **AWS CLI** (the `aws` command), or with an AWS **SDK** (software development kit), a library for your programming language. For Python that's **boto3**:

```python
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

s3.create_bucket(Bucket='crumb-cake-photos-test')
dynamodb.create_table(TableName='cake-photos-test', ...)
lambda_client.create_function(FunctionName='record-cake-photo-test', ...)   # ← fails here
```

This is a real improvement. The setup is now written down, lives in git, and can be re-run. Your teammate writes exactly this script for the test copy. Then the problems show up:

| Problem | What happens at Crumb & Co. |
|---|---|
| **No clean undo** | The script fails on line 3 (a typo in a permission). The bucket and table already exist, the function doesn't. Running the script again fails immediately with "bucket already exists". Someone has to check by hand what got created and delete it before trying again. |
| **No ownership** | Six months later the account has 40 buckets. Is `crumb-cake-photos-test-2` still in use? Which feature does it belong to? Nobody knows, so nobody dares delete it. |
| **No history** | During a busy weekend someone raises the function's timeout in the console to stop errors. The script says 30 seconds; reality says 60. There's no record of who changed it, when, or why. |
| **Can't detect changes** | Because nothing compares "what the script created" with "what's there now", that timeout change stays invisible until it causes the next mystery. |
| **Leftovers cost money** | When the test copy is no longer needed, you delete what you remember. A forgotten test server keeps running and shows up on the bill for months. |

All five problems share one root cause. A script like this is a **list of steps**: create this, then that, then the other. It knows what it did only *while it's running*. Once it finishes, **nothing remembers what was supposed to exist.**

### Era 3: Infrastructure as Code

**Infrastructure as Code (IaC)** fixes the root cause. Instead of writing *steps*, you write a **description of the end result**, and a tool keeps that description and makes reality match it.

Here's an everyday version of the difference. You can get to a friend's house by taking a taxi in two ways:
- **Turn-by-turn directions** ("left at the bakery, right after the bridge, third house"). If one road is closed, the directions break, and nobody else can tell where you were going. This is the **imperative** style of Era 2's scripts.
- **The address.** The driver works out the route, handles closed roads, and anyone who reads the address knows the destination. This is the **declarative** style of IaC.

With IaC, Crumb & Co. writes *"there should be one bucket, one table and one function, configured like this"*. The tool keeps that description, and that's what lets it answer the questions a script never could:

- **What belongs to this feature?** Everything in its description.
- **How do I undo a failed change?** Go back to the previous description, automatically.
- **What changed, and who changed it?** Every change to the description is recorded.
- **Does reality still match?** Compare the two.
- **How do I remove the whole test copy?** Delete its description, and everything in it goes.

A short timeline, so the names you'll meet make sense:

| Year | Milestone |
|---|---|
| 2006 | AWS launches S3 and EC2. Infrastructure is created by clicking or calling APIs. |
| 2011 | **AWS CloudFormation** launches: describe resources in a JSON (later also YAML) **template**, and AWS creates and tracks them. |
| 2013 | The unified **AWS CLI** makes scripting AWS from a terminal easy. |
| 2014 | **Terraform** launches: declarative IaC that works across many cloud providers. |
| 2015 | **boto3**, today's Python SDK, is released. |
| 2019 | **AWS CDK** launches: write IaC in a normal programming language, which generates CloudFormation templates. |

This guide is about the last one. **AWS CDK (Cloud Development Kit)** lets you describe your infrastructure in TypeScript, Python, Java, C# or Go, with loops, functions, classes and editor autocomplete, instead of writing long template files by hand.

## The key idea: CDK writes the plan, CloudFormation does the building

If you remember one thing from this guide, make it this:

> **CDK is a code generator.** Your CDK program runs wherever you run the `cdk` command (your laptop, a virtual machine in the cloud, or a build server in a CI/CD pipeline), and its only job is to produce a JSON file called a **template**. A separate AWS service, **CloudFormation**, reads that template and does the actual creating, updating and deleting, *inside AWS*. CDK itself never creates anything.

```
  Your CDK code    ──cdk synth──►   CloudFormation template   ──cdk deploy──►   CloudFormation   ──►   S3, Lambda,
  (TypeScript, on                   (a JSON file in                             (an AWS service        DynamoDB…
   your machine)                     cdk.out/)                                    that does the work)
```

So CDK work happens in two phases, at different times and in different places:

| | **Synthesize** (`cdk synth`) | **Deploy** (`cdk deploy`) |
|---|---|---|
| Where it runs | Wherever you run `cdk` (laptop, VM or CI server) | Inside AWS (CloudFormation) |
| What it does | Runs your code, writes the template | Reads the template, creates or changes real resources |
| Touches your AWS account? | Barely (reads only) | Yes |
| Typical errors | Code bugs, type errors | "Access denied", "name already taken", limits |
| Analogy | Compiling Java into bytecode | The JVM running that bytecode |

Common trap: expecting deploy-time values, like a real bucket name, to exist during synth (see Step 5).

---

## What we'll build

Crumb & Co.'s cake-photo feature, done properly this time. Whenever a customer uploads a photo to a storage bucket, a function records the file's name, size and upload time in a database table, so the bakers can see every request.

```
 customer uploads ──►  S3 bucket  ──event──►  Lambda function  ──writes──►  DynamoDB table
 a cake photo          (storage)              (runs your Python)            (file name, size, time)
```

Three AWS services, in one sentence each:
- **S3 (Simple Storage Service)** stores files ("objects") in containers called **buckets**.
- **Lambda** runs a piece of your code when something happens. You don't manage a server.
- **DynamoDB** is a fast database that stores items by key, like a giant dictionary.

It's small enough to understand completely, and it touches every core CDK idea: resources, permissions, passing values to running code, events, multiple stacks, and cleanup. We'll call the project `upload-tracker`.

## What you need

| Item | Version / detail | Why |
|---|---|---|
| AWS account | A personal or sandbox account, not your company's production one | Everything gets created here |
| AWS CLI | v2, configured with `aws configure` | Gives CDK your credentials and a default region |
| Node.js | An LTS release (20 or later) | The `cdk` command is a Node.js program, even if you write CDK in Python |
| A code editor | VS Code works well | TypeScript autocomplete catches most mistakes as you type |
| Basic TypeScript | Classes, imports, objects | See the companion post `javascript-vs-typescript.md` |
| Basic Python | Functions, dictionaries | The Lambda function is written in Python |

> 💸 **Cost:** this whole tutorial fits within AWS's free tier for a new account, *if you clean up at the end* (Step 10).

---

## Step 1: Install the CDK command-line tool

The CDK CLI (command-line interface) is the `cdk` command you'll type in a terminal. It runs your code, shows differences, and talks to CloudFormation for you.

```bash
npm install -g aws-cdk
cdk --version
```

### Common questions

**Q: I want to write Python. Why do I need Node.js?**
A: CDK itself is written in TypeScript. Versions for other languages (Python, Java, C#, Go) are generated from that TypeScript by a tool called **jsii**. When you write CDK in Python, your code quietly talks to a Node.js process running the real TypeScript library. So Node.js is always needed.

**Q: Why is TypeScript the default language?**
A: Because it's the original. New features, documentation and examples show up in TypeScript first. Its type checker also catches mistakes, like a misspelled setting name, *in your editor*. In Python you'd find out only when you run the program.

**Q: Do I have to write my Lambda function in TypeScript too?**
A: No, and this trips people up. A CDK project contains **two separate programs**:

| | CDK code | Lambda function code |
|---|---|---|
| Language | TypeScript (here) | Python (here); any Lambda language works |
| Runs where | Wherever you run `cdk` | Inside AWS |
| Runs when | When you synthesize or deploy | Every time the function is triggered |
| Job | *Describe* the infrastructure | *Be* the application |

They never run at the same time. CDK only *defines* the Lambda function. It doesn't care what language the code inside it uses.

**Q: Do I have to run `cdk` on my laptop?**
A: No. It runs anywhere that has Node.js and AWS credentials: your laptop, a cloud virtual machine (for example an EC2 instance you connect to over SSH), or a build server. While you're learning, your laptop is easiest. In companies, production deploys usually come from a **CI/CD pipeline** (an automated system like GitHub Actions or AWS CodePipeline that tests and deploys every merged change), so no individual needs deploy permissions for production. We'll see why that matters in Step 2.

---

## Step 2: Bootstrap your account (once per account and region)

```bash
cdk bootstrap aws://123456789012/us-east-1     # your 12-digit account ID and your region
```

**What "bootstrap" means.** The word comes from the phrase *"pull yourself up by your bootstraps"*: getting started with nothing to lean on. Computers "boot" the same way. A tiny program runs first, and its only job is to load the bigger system.

CDK has a chicken-and-egg problem. To deploy anything, it needs a few things to already exist in your account:
- a **storage bucket** to upload your files to (like your Lambda code), because CloudFormation can only read files from S3, not from the machine where you run `cdk`;
- some **IAM roles** to deploy with. **IAM (Identity and Access Management)** is AWS's permission system, and a **role** is a set of permissions that a person or service can temporarily take on.

But buckets and roles are exactly the kind of thing you'd normally create *with* CDK. `cdk bootstrap` breaks the loop by creating them **once**, as a starter stack named **`CDKToolkit`**. Every later deploy uses it.

### Common questions

**Q: Do I run this for every project?**
A: No. Once per **account + region** pair; that's why the command takes `aws://ACCOUNT/REGION`. If you later deploy to a second region, bootstrap that region too.

**Q: What exactly does it create?**
A: Open **CloudFormation → Stacks → CDKToolkit → Resources** in the console and you'll see roughly:

| Resource | Purpose |
|---|---|
| Staging bucket `cdk-hnb659fds-assets-ACCOUNT-REGION` | Holds files CDK uploads for you (zipped Lambda code, large templates) |
| Container repository `cdk-hnb659fds-container-assets-…` | Holds Docker images, if your app uses them |
| File- and image-publishing roles | Used to upload files and images |
| Lookup role | Read-only; lets CDK look up existing things in your account |
| Deploy role | What `cdk deploy` uses to talk to CloudFormation |
| CloudFormation execution role | What **CloudFormation itself** uses to create your resources. **Has full admin permissions by default.** |

**Q: What is `hnb659fds` in all those names?**
A: It's called a **qualifier**. To see why it exists, start with the problem it solves.

Sometimes two teams share one AWS account but need **separate** bootstrap setups. Say security policy allows Team A's deployments to create only storage and functions, while Team B may also change networking. One `CDKToolkit` stack has one set of roles with one set of permissions, so it can't serve both teams. You need two sets of bootstrap resources side by side, and their names must not collide.

The fix is a **namespace**: a short label built into every name so two copies can coexist. It's like two coworkers named Alex going by "Alex from Sales" and "Alex from IT". The qualifier is that label. `hnb659fds` is just the default: a fixed, meaningless string chosen so it won't clash with names you'd pick yourself. Two teams would bootstrap with their own labels:

```bash
cdk bootstrap --qualifier teama --toolkit-stack-name CDKToolkit-TeamA \
  --cloudformation-execution-policies arn:aws:iam::123456789012:policy/TeamAPolicy
cdk bootstrap --qualifier teamb --toolkit-stack-name CDKToolkit-TeamB \
  --cloudformation-execution-policies arn:aws:iam::123456789012:policy/TeamBPolicy
```

That gives two sets of resources (`cdk-teama-…` and `cdk-teamb-…`), and each team's project points at its own in `cdk.json`:

```json
{ "context": { "@aws-cdk/core:bootstrapQualifier": "teama" } }
```

Most people never change the qualifier. Just recognize it when you see it.

**Q: Why does "full admin by default" matter?**
A: When you run `cdk deploy`, *your own* permissions aren't what create the resources:

```
you ──use──► deploy role ──hand off to──► CloudFormation execution role (admin) ──creates──► resources
```

So **anyone who is allowed to deploy can create anything at all**, with admin power. Picture an intern whose account isn't allowed to create new users. They can still deploy a CDK app that contains this:

```ts
const user = new iam.User(this, 'Backdoor');
user.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'));
```

CloudFormation, running as admin, creates the user, and the intern now has an admin account. **Being allowed to deploy effectively means being admin.** In real companies:
- only an automated CI/CD pipeline (not individual people) is allowed to use the deploy role in production;
- bootstrap uses a narrower policy (`--cloudformation-execution-policies`);
- IAM **permission boundaries** cap what any role CloudFormation creates can do.

For your personal sandbox account, the default is fine.

---

## Step 3: Create a project

```bash
mkdir upload-tracker && cd upload-tracker
cdk init app --language typescript
```

This generates a ready-to-run project. Three files matter:

| File | Role |
|---|---|
| `bin/upload-tracker.ts` | The **entry point**, like `main()`. Creates the **App** and adds **stacks** to it. |
| `lib/upload-tracker-stack.ts` | A **stack**: a class where you declare AWS resources. |
| `cdk.json` | Tells the `cdk` command how to run your app, plus settings (like the qualifier above). |

Three words to learn now:
- **App**: your whole CDK program. One per project.
- **Stack**: a group of resources that is **deployed, updated and deleted together, as one unit**. Each CDK stack becomes exactly one CloudFormation stack, which you can see in the console.
- **Construct**: one building block inside a stack, representing one or more AWS resources (a bucket, a function, or a whole pre-wired pattern).

They nest: **App → Stacks → Constructs**. In fact the App and the stacks are constructs too, so the whole program is one tree. We'll come back to that tree in Step 4.

### Common questions

**Q: How big should a stack be?**
A: Group things that **change together and live together**. Imagine Crumb & Co. a few years from now, grown into a full online store with several engineering teams. Here's how it might split its infrastructure:

| Stack | Contains | Owned by | Changes |
|---|---|---|---|
| `NetworkStack` | Private network (VPC), subnets, gateways | Platform team | A few times a year |
| `DatabaseStack` | Orders database, product catalog table | Data team | Rarely, and carefully |
| `OrdersServiceStack` | Order-processing functions and queues | Orders team | Several times a day |
| `FrontendStack` | Website files and content delivery network | Web team | Daily |
| `MonitoringStack` | Dashboards and alarms | On-call / SRE | As needed |

Why not one giant stack? A deploy succeeds or fails **as a unit**. A typo in a dashboard would then block an urgent fix to order processing, and every deploy would put the database at risk. Separate stacks also mean a team can deploy its piece many times a day without touching anyone else's. There's also a hard limit of 500 resources per stack.

Companies also deploy the **same set of stacks several times**, once per environment (dev, staging, production), usually each in its own AWS account. CDK groups stacks into a **Stage** for this:

```ts
class StoreStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, props);
    const network = new NetworkStack(this, 'Network');
    const db = new DatabaseStack(this, 'Database', { terminationProtection: true });  // blocks accidental deletion
    new OrdersServiceStack(this, 'Orders', { vpc: network.vpc, table: db.ordersTable });
    new FrontendStack(this, 'Frontend');
    new MonitoringStack(this, 'Monitoring');
  }
}
const app = new cdk.App();
new StoreStage(app, 'Dev',  { env: { account: '111111111111', region: 'us-east-1' } });
new StoreStage(app, 'Prod', { env: { account: '222222222222', region: 'us-east-1' } });
```

The same code produces identical dev and production setups. That's the Monday request from Era 1 ("give me a test copy") solved in one line, with no forgotten timeout settings. This repeatability is one of the biggest reasons companies adopt IaC.

---

## Step 4: Declare your first resource, a bucket

Replace the contents of `lib/upload-tracker-stack.ts`:

```ts
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export class UploadTrackerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const uploads = new s3.Bucket(this, 'Uploads', {
      versioned: true,
    });
  }
}
```

Every construct is created the same way, with three arguments: **`(scope, id, props)`**.

```ts
new s3.Bucket(this, 'Uploads', { versioned: true });
//            ^^^^  ^^^^^^^^^  ^^^^^^^^^^^^^^^^^^
//            scope    id            props
```

| Argument | Meaning |
|---|---|
| `scope` | The **parent** in the tree. Almost always `this`, meaning "put me inside this stack." |
| `id` | A name for this building block, unique among its siblings. **Not** the real bucket name. |
| `props` | The settings, the same options you'd fill in on the console's "Create bucket" form. |

The object you get back (`uploads`) represents the bucket. You can read properties from it (`uploads.bucketName`) and call helper methods on it (`uploads.grantRead(...)`).

### Common questions

**Q: In the docs I see both `s3.Bucket` and `s3.CfnBucket`. Which should I use?**
A: CDK has three **levels** of constructs. Think of them as **raw ingredients → a prepared dish → a full meal**.

**Level 1 (L1): `Cfn*` classes**, a one-to-one copy of the raw CloudFormation resource. No defaults, no shortcuts:

```ts
new s3.CfnBucket(this, 'RawBucket', {
  bucketEncryption: {
    serverSideEncryptionConfiguration: [{ serverSideEncryptionByDefault: { sseAlgorithm: 'AES256' } }],
  },
  publicAccessBlockConfiguration: {
    blockPublicAcls: true, blockPublicPolicy: true, ignorePublicAcls: true, restrictPublicBuckets: true,
  },
  versioningConfiguration: { status: 'Enabled' },
});
// Want a function to read this bucket? Write the permission policy by hand.
```

**Level 2 (L2): the regular classes** (`s3.Bucket`, `lambda.Function`). Written by the CDK team on top of L1, with **secure defaults**, friendlier options and **helper methods**. Use these about 90% of the time:

```ts
const bucket = new s3.Bucket(this, 'Bucket', {
  encryption: s3.BucketEncryption.S3_MANAGED,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  versioned: true,
  enforceSSL: true,          // one flag adds a policy that rejects non-HTTPS requests
});
bucket.grantRead(someFunction);   // writes the correct permission policy for you
```

**Level 3 (L3): "patterns"**, one construct that builds a whole common architecture:

```ts
new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'Web', {
  taskImageOptions: { image: ecs.ContainerImage.fromRegistry('nginx') },
  publicLoadBalancer: true,
});
// ~5 lines → a container service, load balancer, network, security groups, roles, logs…
```

| | L1 (`Cfn*`) | L2 | L3 (patterns) |
|---|---|---|---|
| Creates | Exactly 1 resource | 1 main resource (+ helpers) | Many resources |
| Defaults | None | Secure and sensible | Opinionated |
| Effort | High | Low | Lowest |
| Use when | L2 doesn't support a feature yet | Almost always | Your use case matches the pattern |

**Q: The L2 construct doesn't expose a setting I need. Do I have to drop down to L1?**
A: No. Every L2 contains an L1 inside it, and you can reach in to change just that one setting:

```ts
const cfnBucket = bucket.node.defaultChild as s3.CfnBucket;
cfnBucket.analyticsConfigurations = [{ id: 'all', storageClassAnalysis: {} }];
```

This is called the **escape hatch**.

### How it works: the construct tree

Because every construct has a parent (`scope`), your program forms a tree. For our app after Step 6 it will look like this:

```
App
└── UploadTrackerStack                  ← Stack: becomes 1 CloudFormation stack
    ├── Uploads                         ← s3.Bucket (L2)
    │   ├── Resource                    ← the L1 CfnBucket inside it
    │   └── Notifications               ← added automatically when we wire up events
    ├── UploadsTable                    ← dynamodb.TableV2 (L2)
    │   └── Resource
    └── RecordUpload                    ← lambda.Function (L2)
        ├── ServiceRole                 ← an IAM role CDK creates for you
        │   └── DefaultPolicy           ← where permissions get added
        └── Resource                    ← the L1 CfnFunction
```

CDK creates plenty of things you never wrote, like the function's role and its policy. That's part of what L2 constructs do for you, and it's also why it's worth looking at what CDK generates (Step 5).

---

## Step 5: Synthesize and look at the template

```bash
cdk synth
```

This runs your code and writes the template to `cdk.out/UploadTrackerStack.template.json`. Open it. Your three lines of TypeScript became something like:

```json
"Uploads1A2B3C4D": {
  "Type": "AWS::S3::Bucket",
  "Properties": { "VersioningConfiguration": { "Status": "Enabled" } },
  "UpdateReplacePolicy": "Retain",
  "DeletionPolicy": "Retain"
}
```

### Common questions

**Q: I added `console.log(uploads.bucketName)` and it printed `${Token[TOKEN.180]}`. Is that a bug?**
A: No. This is the synth-vs-deploy split from the key idea at the start. Your code runs during *synthesis*, and **the bucket doesn't exist yet**, so it has no name to give you. CDK hands you a **token** instead: a placeholder that means "the real value will go here later." Here's one value's whole journey:

1. **In your code (synth, on your machine):** `uploads.bucketName` → `${Token[TOKEN.180]}`
2. **In the template:** CDK swaps the token for a CloudFormation instruction, `{ "Ref": "Uploads1A2B3C4D" }`. It means "once you've created the resource called `Uploads1A2B3C4D`, put its name here." (An ARN, AWS's full ID for a resource, becomes `{ "Fn::GetAtt": ["Uploads1A2B3C4D", "Arn"] }`.)
3. **During deploy (in AWS):** CloudFormation creates the bucket, gets back its real name, say `uploadtrackerstack-uploads1a2b3c4d-9xk2m7q1`, and fills it in.
4. **When your function runs:** the function reads that real name (we'll set this up in Step 6).

Think of a token as a spreadsheet formula like `=A1`. You can copy the formula into other cells and it stays correct, but you can't see the number until the sheet is calculated (deployed).

What follows from that:
- ✅ You **can** pass tokens anywhere CDK expects a value: settings, permissions, environment variables, even inside strings like `` `${bucket.bucketArn}/*` ``.
- ❌ You **can't** use them in your own logic. `if (uploads.bucketName.startsWith('prod'))` compares against the placeholder text and will never be true.
- 👀 To see the real value after deploying, add an **output**. `cdk deploy` prints it:
  ```ts
  new cdk.CfnOutput(this, 'BucketName', { value: uploads.bucketName });
  ```

**Q: Why does the template say `Uploads1A2B3C4D` and not just `Uploads`?**
A: One resource has **three different names**:

| Name | Example | Created by | Used for |
|---|---|---|---|
| Construct id | `Uploads` | You | Your code |
| Logical ID | `Uploads1A2B3C4D` | CDK, during synth | Identifying the resource *inside the template* |
| Physical name | `uploadtrackerstack-uploads1a2b3c4d-9xk2m7q1` | CloudFormation, during deploy | The real name in AWS |

The **logical ID** is the construct's position in the tree plus a short **hash** (a fingerprint calculated from that position). The hash isn't random: the same position always gives the same hash, on every machine, every time. That stability is the whole point. It's how CloudFormation recognizes "this is the same bucket as last time" and *updates* it instead of creating a new one. The hash also prevents clashes: `A/BC` and `AB/C` would both flatten to `ABC`, but their hashes differ.

The **physical name** *does* include a random suffix, and CloudFormation adds it for three reasons:
1. **Bucket names are unique across all of AWS, worldwide.** `uploads` is certainly taken.
2. **Safe replacement.** When a resource has to be replaced, CloudFormation creates the new one *before* deleting the old one, so the two need different names.
3. **Multiple copies.** You can deploy `Dev` and `Prod` copies into one account without clashes.

CloudFormation keeps the mapping *logical ID → physical name* for every stack. You can see it in the console under **Resources** ("Logical ID" and "Physical ID" columns). That mapping is the stack's memory.

> ⚠️ **Never rename a construct `id` after deploying.** Changing `'Uploads'` to `'UserUploads'` changes the logical ID. CloudFormation sees "old bucket gone, new bucket appeared" and **creates a brand-new, empty bucket**, then drops the old one from the stack. Your app suddenly points at an empty bucket. Step 9 shows how to catch this before it happens.

**Q: Do I have to run `cdk synth` before every deploy?**
A: No, `cdk deploy` synthesizes automatically. Running `synth` yourself is for looking at the template.

---

## Step 6: Add the table and the function, then deploy

Now the real app. First the function code. Create `lambda/index.py`:

```python
import os
import urllib.parse
import boto3

table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])

def handler(event, context):
    for record in event['Records']:
        obj = record['s3']['object']
        table.put_item(Item={
            'fileKey': urllib.parse.unquote_plus(obj['key']),   # S3 URL-encodes key names
            'sizeBytes': obj.get('size', 0),
            'uploadedAt': record['eventTime'],
        })
```

Then update the stack:

```ts
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class UploadTrackerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const uploads = new s3.Bucket(this, 'Uploads', {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,   // see Step 10
      autoDeleteObjects: true,
    });

    const table = new dynamodb.TableV2(this, 'UploadsTable', {
      partitionKey: { name: 'fileKey', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const recordUpload = new lambda.Function(this, 'RecordUpload', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',                    // file index.py, function handler
      code: lambda.Code.fromAsset('lambda'),       // CDK zips this folder and uploads it
      environment: { TABLE_NAME: table.tableName },
    });

    table.grantWriteData(recordUpload);
    uploads.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.LambdaDestination(recordUpload));

    new cdk.CfnOutput(this, 'BucketName', { value: uploads.bucketName });
    new cdk.CfnOutput(this, 'TableName', { value: table.tableName });
  }
}
```

Deploy it:

```bash
cdk deploy
```

CDK shows the permission changes it's about to make and asks you to confirm. Then it prints progress and, at the end, your outputs:

```
Outputs:
UploadTrackerStack.BucketName = uploadtrackerstack-uploads1a2b3c4d-9xk2m7q1
UploadTrackerStack.TableName  = UploadTrackerStack-UploadsTable7F3A9B2C-1QW2E3R4T5Y6
```

### Common questions

**Q: How does the Python code know the table's name, when that name is only decided during deploy?**
A: Through an **environment variable**, a named value that a program can read from its surroundings. (Same idea as `PATH` on Linux.) Follow the token from Step 5:

```
TypeScript   environment: { TABLE_NAME: table.tableName }     ← a token
   ↓ synth
Template     "TABLE_NAME": { "Ref": "UploadsTable7F3A9B2C" }   ← an instruction
   ↓ deploy
Lambda       TABLE_NAME = UploadTrackerStack-UploadsTable…    ← real value, saved in the function's settings
   ↓ every run
Python       os.environ['TABLE_NAME']
```

Environment variables are the **bridge between the two programs** from Step 1. They're the standard way to pass anything CDK knows (names, addresses, settings) to your running code, without hard-coding it.

**Q: What if I forget `table.grantWriteData(recordUpload)`?**
A: The deploy succeeds, but every upload makes the function fail with `AccessDeniedException ... not authorized to perform: dynamodb:PutItem`. Here's why. Every Lambda function runs as an IAM role. The role CDK creates for you (`ServiceRole` in the tree) only starts with permission to write logs. **In AWS, everything is denied unless something allows it.**

`grantWriteData` adds a policy to that role that allows the write actions (`PutItem`, `UpdateItem`, `DeleteItem`, `BatchWriteItem` and a few related ones), on **this table only**. That's the principle of **least privilege**: give exactly the access needed, no more. You'll see tutorials that write `actions: ['dynamodb:*']` or `['s3:*']` by hand. It works, but it lets the function delete the whole table or rewrite a bucket's security policy. Prefer the `grant*` methods.

**Q: The function needs permission to write to the table. Doesn't S3 also need permission to *call* the function?**
A: Yes, and CDK handled it. There are two directions of permission:
- **What the function may do:** an *identity-based* policy on the function's role. `grantWriteData` added that.
- **Who may call the function:** a *resource-based* policy on the function itself. `LambdaDestination` added one saying "this bucket may invoke this function."

Mixing these two up is the cause of a large share of "access denied" puzzles on AWS.

**Q: Why do S3 permission policies often list two ARNs, `arn:aws:s3:::my-bucket` and `arn:aws:s3:::my-bucket/*`?**
A: An **ARN (Amazon Resource Name)** is a resource's full ID: `arn:partition:service:region:account:resource`. S3 permissions apply to two kinds of things:

| ARN | Refers to | Used by actions like |
|---|---|---|
| `arn:aws:s3:::my-bucket` | The bucket itself | `ListBucket` |
| `arn:aws:s3:::my-bucket/*` | The files *inside* the bucket | `GetObject`, `PutObject` |

If a policy lists only the first, reading or writing files is denied. The `grant*` methods include both for you. And the `:::` in S3 ARNs? Bucket names are globally unique, so the region and account parts are simply left empty.

### How it works: what `cdk deploy` actually does

1. **Synthesize**: runs your code and writes the template.
2. **Upload files**: zips `lambda/` and uploads it to the bootstrap staging bucket from Step 2.
3. **Create a change set**: CloudFormation compares the new template with what's already deployed. For each resource it decides *add*, *modify* or *remove*, and for each modification, whether it can **update in place** or must **replace**.
4. **Execute**: CloudFormation works out the order from the references (the function refers to the table, so the table comes first) and builds independent things in parallel. It doesn't follow the order you wrote them in.
5. **Roll back on failure**: if anything fails, CloudFormation returns the stack to how it was before the deploy. No more half-finished setups like the failed script in Era 2.

---

## Step 7: Try it

```bash
aws s3 cp cake.jpg s3://<BucketName from the outputs>/     # any photo works

aws dynamodb scan --table-name <TableName from the outputs>
```

You should see an item with `fileKey: cake.jpg`, its size and a timestamp: the bakers' first cake request. If not, check the function's logs:

```bash
aws logs tail /aws/lambda/<function name> --follow
```

(You'll find the function's physical name in the console under **CloudFormation → UploadTrackerStack → Resources**.)

### Common questions

**Q: Can I edit the function's settings in the console to debug faster?**
A: Don't. The stack's template says what the function should look like, and a manual edit makes reality disagree with it. That's called **drift** (Step 9). Change the code and run `cdk deploy` again. For quick iteration while developing, `cdk watch` redeploys automatically every time you save a file.

---

## Step 8: Split into two stacks

The feature is a hit, and the owner wants more: resize photos, email the bakers, tag rush orders. The processing logic will now change every week. The table of cake requests is the bakery's real business data and should rarely be touched. Two different lifecycles belong in two stacks, so let's move the table into its own.

`lib/data-stack.ts`:

```ts
export class DataStack extends cdk.Stack {
  public readonly table: dynamodb.TableV2;           // expose it so other stacks can use it

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    this.table = new dynamodb.TableV2(this, 'UploadsTable', {
      partitionKey: { name: 'fileKey', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
  }
}
```

`lib/ingest-stack.ts`:

```ts
export interface IngestStackProps extends cdk.StackProps {
  table: dynamodb.ITableV2;                           // receive the table, not a string
}

export class IngestStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: IngestStackProps) {
    super(scope, id, props);
    const uploads = new s3.Bucket(this, 'Uploads', {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });
    const recordUpload = new lambda.Function(this, 'RecordUpload', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda'),
      environment: { TABLE_NAME: props.table.tableName },
    });
    props.table.grantWriteData(recordUpload);
    uploads.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.LambdaDestination(recordUpload));
  }
}
```

`bin/upload-tracker.ts`:

```ts
const app = new cdk.App();
const data = new DataStack(app, 'Data');
new IngestStack(app, 'Ingest', { table: data.table });
```

The app no longer defines `UploadTrackerStack`, but removing a stack from your code **doesn't delete it from AWS**. CDK only deploys what's in the app. So destroy the old stack first, then deploy the new pair:

```bash
cdk destroy UploadTrackerStack
cdk deploy --all
```

### Common questions

**Q: The two stacks deploy separately. How does `Ingest` get the table's name from `Data`?**
A: It looks like ordinary object-oriented code: one class exposes a property and another receives it. But two stacks can't share memory, because they're deployed separately. So when a token crosses a stack boundary, CDK quietly generates:
1. an **export** in `Data` (a named value CloudFormation publishes, like "Data:ExportsOutput…TableName…");
2. an **import** of that export in `Ingest`;
3. a **dependency**, so `cdk deploy --all` always deploys `Data` first.

You could write exports and imports by hand (`CfnOutput` with `exportName`, plus `Fn.importValue`), but passing objects through props is safer. CDK picks the names, tracks the order, and TypeScript checks you passed the right type.

**Q: Why pass the table object instead of just its name as a string?**
A: With the object, the receiving stack can call `grantWriteData` and read `tableName`, and everything is type-checked. With a plain string, you'd have to write permissions by hand. Notice the prop's type is `ITableV2`, an **interface**. A table you create and a table you merely look up (`TableV2.fromTableName(...)`) both fit it, so `IngestStack` doesn't care which it gets.

**Q: Why put the bucket and the function together, rather than the bucket with the table?**
A: To avoid a **circular dependency**. The bucket's event setup needs to know the function (to call it), and the function's permission needs to know the bucket (who may call it). With the bucket in one stack and the function in another, each stack would need the other deployed first. CDK refuses this with a "cyclic reference" error. **Keep tightly-coupled resources in the same stack.**

**Q: I removed the table from `Ingest` and now `cdk deploy` fails, saying the export is in use. What happened?**
A: This is nicknamed the **"deadly embrace"**. Removing the reference makes CDK delete the export from `Data`. But `Data` deploys *first*, while `Ingest` still imports the export, and CloudFormation refuses to delete an export that's in use. The fix takes two deploys:
1. Keep the export alive on purpose. In `DataStack` add `this.exportValue(this.table.tableName)` and deploy (`Ingest` stops importing it).
2. Remove that line and deploy again.

**Q: Does the table keep its data when it moves to the new stack?**
A: No. Each stack tracks only its own resources. To CloudFormation, the table in `Data` is a brand-new resource, so it creates a new, empty table, even though the code looks identical. That's fine for a tutorial. For real data you'd have to migrate it, or use CloudFormation's *resource import* to hand an existing table to the new stack. This is why stack boundaries are worth deciding early.

---

## Step 9: Change things safely

### Before every deploy: `cdk diff`

```bash
cdk diff
```

`cdk diff` compares **your local code** with **what's currently deployed** and lists every resource that would be added, modified or removed. Pay special attention to anything marked as being **replaced**. Some changes can't be made in place, like a table's partition key, a bucket's name or a server's operating-system image. CloudFormation then creates a new resource and deletes the old one. For anything that holds data, that means data loss. **Make `cdk diff` a habit before every deploy that touches data.**

### Drift: when reality and the template disagree

**Drift** means the real resources in AWS no longer match the stack's template, because someone changed them outside CloudFormation (usually by clicking in the console). **Drift detection** is a CloudFormation feature that checks each resource. It reports `IN_SYNC`, `MODIFIED` (showing the expected and actual values) or `DELETED`.

Remember the busy weekend in Era 2, when someone raised the function's timeout in the console and nobody noticed? With CDK, drift detection would report the function as `MODIFIED`: *expected 30 seconds, actual 60*.

There are really **three versions** of your setup, and each tool compares a different pair:

```
 (1) Your local CDK code        ← what you're editing
          │   cdk diff            compares (1) with (2)
          ▼
 (2) Deployed template          ← what CloudFormation last deployed
          │   drift detection     compares (2) with (3)
          ▼
 (3) Real resources in AWS      ← what actually exists
```

Run drift detection from the console (**CloudFormation → your stack → Stack actions → Detect drift**) or the CLI (`aws cloudformation detect-stack-drift --stack-name Ingest`).

### Common questions

**Q: Does drift detection compare my code with what's in AWS?**
A: No. It compares the *last deployed template* with reality. Edits you haven't deployed yet are invisible to it; `cdk diff` shows those. Drift detection also mainly checks the settings that the template explicitly sets, and not every resource type supports it.

**Q: A teammate turned on a setting by hand. Will my next `cdk deploy` undo it?**
A: Usually not. A deploy applies only the **change set**, the resources *your code changed*. If you only touched the function, the drifted bucket is left alone and the drift stays. To resolve it, either put the setting in your code and deploy, or undo the manual change by hand.

**Q: Does it run automatically?**
A: Not by default. Teams schedule it with the AWS Config rule `cloudformation-stack-drift-detection-check`, which flags drifted stacks for them.

**Q: Why do people keep saying "never change CDK-managed resources by hand"?**
A: Besides causing confusion, drift can leave a stack **stuck**. When a deploy fails, CloudFormation rolls back by restoring the previous template. If someone manually deleted a resource that template depends on, the rollback itself fails, and the stack ends up in `UPDATE_ROLLBACK_FAILED`:

```
UPDATE_IN_PROGRESS ─► UPDATE_COMPLETE                                  (normal)
        └─► UPDATE_ROLLBACK_IN_PROGRESS ─► UPDATE_ROLLBACK_COMPLETE      (failed, safely undone)
                         └─► UPDATE_ROLLBACK_FAILED                      (stuck!)
```

You can recover with **Stack actions → Continue update rollback** (optionally skipping the broken resources), or by deleting and redeploying the stack. The simplest prevention: change the code, not the console.

---

## Step 10: Clean up

```bash
cdk destroy --all
```

CloudFormation deletes stacks in reverse dependency order (`Ingest` first, then `Data`). Each resource then follows its **removal policy**:

| Policy | What happens to the resource | CDK default for |
|---|---|---|
| `RETAIN` | Left in AWS. CloudFormation just stops managing it. | Things that hold data: S3 buckets, DynamoDB tables |
| `DESTROY` | Deleted | Most other resources |
| `SNAPSHOT` | Backed up, then deleted | Databases and disk volumes that support it |

That's why we set `removalPolicy: DESTROY` on the bucket and table in this tutorial. Without it, they'd survive `cdk destroy` and keep costing (a little) money. The safe default exists so you never lose production data by accident.

Compare this with Era 2, when the test copy was cleaned up from memory and a forgotten server stayed on the bill for months. Here the stack knows everything it created, so one command removes it all. The few exceptions are listed below, so nothing surprises you.

### Common questions

**Q: I set `DESTROY` on a bucket, but `cdk destroy` failed with `BucketNotEmpty`.**
A: S3 refuses to delete a bucket that still contains files, and the stack ends up in `DELETE_FAILED`. That's why we also set `autoDeleteObjects: true`. It makes CDK add a small helper (a **custom resource**, a Lambda function CloudFormation runs during deployment) that empties the bucket right before it's deleted.

**Q: After destroying, I still see `/aws/lambda/...` logs in CloudWatch. Why?**
A: The Lambda service creates that log group the first time your function runs. CloudFormation never created it, so it doesn't know to delete it. Delete it by hand, or create the log group in CDK (`logGroup: new logs.LogGroup(...)` on the function) so the stack owns it.

**Q: Will `cdk destroy` ever delete something I didn't create with CDK?**
A: No. Resources you merely *reference*, like `s3.Bucket.fromBucketName(this, 'Existing', 'some-bucket')`, are lookups. CDK never creates or deletes them. CDK manages what it created, and nothing else.

---

## A bigger example: a load-balanced website

To see how much CDK does for you, here's a classic setup from the [aws-devops-zero-to-hero](https://github.com/iam-veeramalla/aws-devops-zero-to-hero) course (Day 24). There's a private network with two public subnets in two **availability zones** (separate data centers in one region). There are two web servers, one per zone. A **load balancer** spreads visitors across them. The course builds it with Terraform in about 17 hand-written resources and 130 lines. In CDK:

```ts
// Network: rarely changes
export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    this.vpc = new ec2.Vpc(this, 'Vpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      maxAzs: 2,
      natGateways: 0,  // the default would add NAT gateways, roughly $30+/month each
      subnetConfiguration: [{ name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 }],
    });
  }
}

// Web tier: changes often
export interface WebStackProps extends cdk.StackProps { vpc: ec2.IVpc; }

export class WebStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: WebStackProps) {
    super(scope, id, props);
    const { vpc } = props;

    const albSg = new ec2.SecurityGroup(this, 'AlbSg', { vpc });
    albSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'HTTP from the internet');

    const webSg = new ec2.SecurityGroup(this, 'WebSg', { vpc });
    webSg.addIngressRule(albSg, ec2.Port.tcp(80), 'HTTP from the load balancer only');

    const makeServer = (id: string, subnet: ec2.ISubnet, script: string) =>
      new ec2.Instance(this, id, {
        vpc,
        vpcSubnets: { subnets: [subnet] },
        securityGroup: webSg,
        instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
        machineImage: ec2.MachineImage.latestAmazonLinux2023(),
        userData: ec2.UserData.custom(fs.readFileSync(script, 'utf8')),
      });
    const web1 = makeServer('WebServer1', vpc.publicSubnets[0], 'userdata.sh');
    const web2 = makeServer('WebServer2', vpc.publicSubnets[1], 'userdata1.sh');

    const alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', { vpc, internetFacing: true, securityGroup: albSg });
    alb.addListener('Http', { port: 80 }).addTargets('Web', {
      port: 80,
      targets: [new targets.InstanceTarget(web1), new targets.InstanceTarget(web2)],
      healthCheck: { path: '/' },
    });

    new cdk.CfnOutput(this, 'LoadBalancerDns', { value: alb.loadBalancerDnsName });
  }
}
```

And the construct tree it produces. Most of it you never wrote:

```
App
├── Network
│   └── Vpc                           ← you wrote one construct…
│       ├── Resource                  (the VPC)
│       ├── PublicSubnet1             ← …and CDK generated the rest
│       │   ├── Subnet                (zone a)
│       │   ├── RouteTable
│       │   ├── RouteTableAssociation
│       │   └── DefaultRoute          (internet traffic → gateway)
│       ├── PublicSubnet2             (same, zone b)
│       ├── IGW                       (internet gateway)
│       └── VPCGW                     (attaches the gateway to the VPC)
└── Web
    ├── AlbSg, WebSg                  (firewall rules)
    ├── WebServer1
    │   ├── InstanceRole              (IAM role, auto-created)
    │   ├── InstanceProfile
    │   └── Resource                  (the server)
    ├── WebServer2                    (same)
    ├── Alb
    │   ├── Resource                  (the load balancer)
    │   └── Http                      (listener on port 80)
    │       └── WebGroup              (target group + both servers)
    └── LoadBalancerDns               (output)
```

Takeaways:
- **One L2 construct can mean a dozen real resources.** That's leverage, and it's also why you should read what CDK generates. The default VPC would have quietly added NAT gateways that cost money.
- **Security comes almost free.** Only the load balancer is open to the internet; the servers accept traffic only from the load balancer's firewall group. (The original demo opened web and SSH ports on the servers to everyone.)
- **`vpc` crosses from `Network` to `Web`** exactly like our table did in Step 8.

---

## CDK compared with other IaC tools

| | CloudFormation (raw) | AWS CDK | Terraform |
|---|---|---|---|
| You write | YAML / JSON | TypeScript, Python, Java, C#, Go | HCL (`.tf` files) |
| Abstraction | Raw resources only | L1 / L2 / L3 constructs | Resources + modules |
| Clouds | AWS | AWS (through CloudFormation) | Many (AWS, Azure, GCP…) |
| Who stores the state | AWS (the stack) | AWS (the stack) | **You** (a state file, often kept in S3) |
| Preview changes | Change set | `cdk diff` | `terraform plan` |
| Apply changes | Create / update stack | `cdk deploy` | `terraform apply` |
| Detect drift | Detect drift | Detect drift (via CloudFormation) | `terraform plan -refresh-only` |

All three are declarative, all three keep a record of what they manage, and all three warn when a change forces replacement. The idea you learned here carries over.

---

## Common mistakes

1. **Hard-coding names** (`bucketName: 'my-bucket'`). It can collide with anyone's bucket worldwide, blocks safe replacement, and breaks dev/prod copies. Let CloudFormation name things, and pass names around with tokens and environment variables.
2. **Using a token in your own logic.** `if`, `.split()` and `.length` on a token act on the placeholder, not the real value.
3. **Granting `*` permissions by hand** instead of using `grant*` methods.
4. **Renaming construct ids** or moving constructs after deploying. That replaces the resource.
5. **Expecting `DESTROY` to delete a non-empty bucket.** Add `autoDeleteObjects: true`.
6. **Editing CDK-managed resources in the console.** That causes drift, surprises and stuck stacks.
7. **Old Lambda runtimes.** Copy-pasted examples often use runtimes past end of support (like `PYTHON_3_9`). Use a current one (`PYTHON_3_12` or newer).
8. **Passing an ARN where a name is needed**, then string-splitting it in your function. Pass `bucket.bucketName` or `table.tableName` directly.

---

## Command cheat sheet

| Command | What it does |
|---|---|
| `cdk bootstrap aws://ACCOUNT/REGION` | One-time setup per account + region |
| `cdk init app --language typescript` | Create a new project |
| `cdk ls` | List the stacks in your app |
| `cdk synth` | Generate templates into `cdk.out/` |
| `cdk diff` | Compare local code with what's deployed (watch for replacements!) |
| `cdk deploy` / `cdk deploy --all` | Deploy one or all stacks |
| `cdk watch` | Redeploy on every save (development only) |
| `cdk destroy` / `cdk destroy --all` | Delete stacks, following removal policies |
| `aws cloudformation detect-stack-drift --stack-name X` | Check a stack for drift |

---

## Check yourself

Try answering before opening the answers.

1. `console.log(table.tableName)` prints `${Token[TOKEN.42]}`. Why, and when does the real name exist?
2. You rename `new s3.Bucket(this, 'Uploads')` to `new s3.Bucket(this, 'UserUploads')` and deploy. What happens to your files, and which command would have warned you?
3. Your function fails with `AccessDeniedException` on `dynamodb:PutItem`. What's missing?
4. Why do S3 policies often list both `arn:aws:s3:::bucket` and `arn:aws:s3:::bucket/*`?
5. A teammate enables bucket versioning in the console. You change the function's memory in code but haven't deployed. Which tool shows each change, and does your next deploy undo the versioning?
6. Someone can't create IAM users but is allowed to run `cdk deploy`. Can they become admin? How do companies prevent this?
7. Why did we keep the bucket and the function in the same stack in Step 8?
8. After `cdk destroy --all`, what's left in your account, and why?

<details>
<summary><b>Answers</b></summary>

1. Your code runs during synthesis, before anything exists, so CDK returns a placeholder (token). It becomes `{"Ref": …}` in the template, and CloudFormation fills in the real name **during deploy**. Use a `CfnOutput` to see it.
2. The logical ID changes, so CloudFormation creates a **new, empty bucket**. The old one is dropped from the stack (kept in AWS if its policy is `RETAIN`, deleted if `DESTROY`). Either way your app now points at an empty bucket. `cdk diff` would have shown one bucket removed and one added.
3. The function's role has no permission to write to the table. Add `table.grantWriteData(fn)`.
4. Bucket-level actions (like listing) apply to the bucket ARN; file-level actions (get, put) apply to `bucket/*`.
5. Versioning → **drift detection** (deployed template vs. reality). Memory → **`cdk diff`** (code vs. deployed template). The deploy applies only the memory change, so the versioning drift remains.
6. Yes. They deploy a stack that creates an admin user, and CloudFormation's execution role (admin by default) creates it. Prevention: only CI/CD may deploy to production, a narrower bootstrap execution policy, and permission boundaries.
7. The bucket's event setup references the function, and the function's invoke permission references the bucket. Split across stacks, that's a circular dependency.
8. The function's CloudWatch log group, because Lambda created it at runtime, not CloudFormation. Also anything with a `RETAIN` policy, anything you only referenced, and the `CDKToolkit` bootstrap stack.

</details>

---

## References

- [AWS CDK v2 Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html): concepts, getting started, best practices
- [AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/): every construct and its options
- [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html): what bootstrap creates and how to customize it
- [AWS CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html): stacks, change sets, drift detection
- [iam-veeramalla/aws-devops-zero-to-hero](https://github.com/iam-veeramalla/aws-devops-zero-to-hero): Day 11 (CloudFormation) and Day 24 (Terraform) for comparison
- My cloud computing course notes on AWS CDK
