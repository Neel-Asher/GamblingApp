class ValidationResult:

    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, error):
        self.errors.append(error)

    def add_warning(self, warning):
        self.warnings.append(warning)

    def is_valid(self):
        return len(self.errors) == 0

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings