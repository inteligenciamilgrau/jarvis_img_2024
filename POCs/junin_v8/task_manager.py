import importlib.util
import os

class TaskManager:
    def __init__(self, tasks_path='tasks_folder', prompt_file='system_prompt.txt'):
        current_dir = os.path.dirname(__file__)
        self.tasks_path = os.path.join(current_dir, tasks_path)
        self.prompt_file = os.path.join(current_dir, prompt_file)

        # Load task handlers and their metadata
        self.task_handlers = self.load_task_handlers(self.tasks_path)
        #print("HANDLERS", self.task_handlers)
    
    def load_task_handlers(self, tasks_path):
        handlers = {}
        for filename in os.listdir(tasks_path):
            if filename.endswith('.py'):
                task_name = filename[:-3]  # Remove '.py' extension
                module_path = os.path.join(tasks_path, filename)
                spec = importlib.util.spec_from_file_location(task_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Load metadata and the execute function
                handlers[task_name] = {
                    'description': getattr(module, 'description', 'No description provided.'),
                    'trigger': getattr(module, 'trigger', 'No trigger provided.'),
                    'example': getattr(module, 'example', 'No example provided.'),
                    'execute': getattr(module, 'execute')
                }
        return handlers
    
    def load_system_prompt(self):
        """Load the basic system prompt from an external text file."""
        try:
            with open(self.prompt_file, 'r') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"The system prompt file '{self.prompt_file}' does not exist.")

    def build_system_prompt(self):
        """Build a dynamic system prompt with descriptions, triggers, and examples for each task."""
        #prompt = "You are a helpful assistant. Respond in JSON format based on the type of request.\n\n"

        # Load task handlers and their metadata
        self.task_handlers = self.load_task_handlers(self.tasks_path)

        prompt = self.load_system_prompt() + "\n\n"
        prompt += "The available tasks are as follows:\n"
        for task_name, task_info in self.task_handlers.items():
            prompt += f"Task: {task_name}\n"
            prompt += f"Description: {task_info['description']}\n"
            prompt += f"Trigger: {task_info['trigger']}\n"
            prompt += f"Example: {task_info['example']}\n\n"
        return prompt

    def execute_task(self, task_type, content):
        """Execute the appropriate task based on task type."""
        if task_type in self.task_handlers:
            return self.task_handlers[task_type]['execute'](content)
        else:
            return f"Unknown task type: {task_type}"
