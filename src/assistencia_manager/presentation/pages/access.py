from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from assistencia_manager.domain.entities.access import UserRole

class AccessPage(QWidget):
    def __init__(self, access_service=None, audit_service=None):
        super().__init__(); self.access_service = access_service; self.audit_service = audit_service
        self.name = QLineEdit(); self.username = QLineEdit(); self.credential_input = QLineEdit(); self.credential_input.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout(); form.addRow("Nome", self.name); form.addRow("Usuário", self.username); form.addRow("Senha", self.credential_input)
        button = QPushButton("Criar usuário administrador"); button.clicked.connect(self.create_user)
        self.message = QLabel(); self.table = QTableWidget(0, 3); self.table.setHorizontalHeaderLabels(("Usuário", "Perfil", "Ativo"))
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Usuários e auditoria")); layout.addLayout(form); layout.addWidget(button); layout.addWidget(self.message); layout.addWidget(self.table)
        self.refresh()
    def create_user(self):
        if self.access_service is None: return
        try: self.access_service.create_user(self.name.text(), self.username.text(), self.credential_input.text(), UserRole.ADMIN); self.message.setText("Usuário criado"); self.refresh()
        except Exception as error: self.message.setText(str(error))
    def refresh(self):
        if self.access_service is None: return
        users = self.access_service.list_users(); self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            for col, value in enumerate((user.username, user.role.value, "sim" if user.active else "não")): self.table.setItem(row, col, QTableWidgetItem(value))
