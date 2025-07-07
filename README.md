# Waystation (`way`)

Explore, map, plan, edit and share your codebase.

## Features

### Explore 
- Navigate through your codebase with ease.
- View file contents and metadata.
- Powered by ripgrep.

### Map
- Save waypoints in your codebase.
- Step through the flow of your code.
- Document the journey through your codebase.

### Plan
- Use steps to understand the flow of your code.
- Create a plan for your next coding task.
- Share your plan with others.

### Edit
- Edit files directly from the Waystation.
- Map our your changes and edit in the order that makes sense.

### Share
- Share your flow with others.
- Help onboarding new team members.
- Share your plan with others.
- Describe how things work interactively.

## Installation
1. Clone the repository:
   ```bash
   git clone
   ```
2. Navigate to the project directory:
   ```bash
    cd waystation
    ```
3. Install the dependencies:
   ```bash
   brew install ripgrep bat grep-ast
   ```

4. Run the application:
   ```bash
    way <pattern> [<path>]
    ```


## Usage
- To explore your codebase, run:
  ```bash
  ws <pattern> [<path>]
  ```
  Replace `<pattern>` with the search term and `<path>` with the directory you want to search in.
