import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_STYLE = """
QMainWindow {
    background-color: #F3F4F6;
}

QWidget {
    background-color: #F3F4F6;
    color: #1F2937;
    font-family: "Segoe UI";
    font-size: 13px;
}

QLabel {
    background-color: transparent;
}

QScrollArea {
    border: none;
    background-color: #F3F4F6;
}

QScrollArea > QWidget > QWidget {
    background-color: #F3F4F6;
}

QFrame#Card {
    background-color: #FFFFFF;
    border: 1px solid #D6DBE3;
    border-radius: 4px;
}

QFrame#HeroCard {
    background-color: #ECEFF3;
    border: 1px solid #D2D8E0;
    border-radius: 4px;
}

QFrame#DropArea {
    background-color: #FAFBFC;
    border: 1px dashed #9AA4B2;
    border-radius: 4px;
}

QFrame#DropArea:hover {
    border: 1px dashed #64748B;
    background-color: #F1F5F9;
}

QLabel#AppTitle {
    font-size: 22px;
    font-weight: 800;
    color: #111827;
}

QLabel#PageTitle {
    font-size: 17px;
    font-weight: 800;
    color: #111827;
}

QLabel#Muted {
    color: #5F6B7A;
}

QLabel#SmallMuted {
    color: #6B7280;
    font-size: 12px;
}

QLabel#SectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #1F2937;
}

QPushButton {
    border: 1px solid #BFC7D1;
    border-radius: 4px;
    padding: 7px 11px;
    font-weight: 700;
    background-color: #FFFFFF;
    color: #1F2937;
}

QPushButton#PrimaryButton {
    background-color: #46596C;
    border: 1px solid #394A5B;
    color: #FFFFFF;
}

QPushButton#PrimaryButton:hover {
    background-color: #394A5B;
}

QPushButton#SecondaryButton {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #BFC7D1;
}

QPushButton#SecondaryButton:hover {
    background-color: #F3F5F8;
}

QPushButton#DangerButton {
    background-color: #FFFFFF;
    color: #7A2E2E;
    border: 1px solid #C9A5A5;
}

QPushButton#DangerButton:hover {
    background-color: #F7EEEE;
}

QPushButton:disabled {
    background-color: #E5E7EB;
    border: 1px solid #D1D5DB;
    color: #9CA3AF;
}

QPushButton#FormatOptionButton {
    background-color: #FFFFFF;
    border: 1px solid #BFC7D1;
    border-radius: 4px;
    padding: 7px 10px;
    color: #1F2937;
    font-weight: 800;
    text-align: center;
}

QPushButton#FormatOptionButton:hover {
    border: 1px solid #8DA3BD;
    background-color: #F3F6FA;
}

QPushButton#FormatOptionButton:checked {
    background-color: #E3E8ED;
    border: 1px solid #7D8B99;
    color: #2F455A;
}

QPushButton#FormatOptionButton:disabled {
    background-color: #E5E7EB;
    border: 1px solid #D1D5DB;
    color: #9CA3AF;
}

QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #D6DBE3;
    border-radius: 4px;
    padding: 6px;
}

QListWidget::item {
    padding: 7px;
    margin: 3px;
    border-radius: 3px;
    background-color: #F7F8FA;
    color: #1F2937;
}

QListWidget::item:selected {
    background-color: #E3E8ED;
    color: #2F455A;
}

    QTextEdit {
        background-color: #FFFFFF;
        border: 1px solid #D6DBE3;
        border-radius: 4px;
        padding: 6px;
        color: #1F2937;
        font-family: Consolas, "Courier New";
        font-size: 12px;
}

QProgressBar {
    background-color: #E5E7EB;
    border: 1px solid #C9D0DA;
    border-radius: 4px;
    height: 18px;
    text-align: center;
    color: #1F2937;
    font-weight: 700;
}

QProgressBar::chunk {
    background-color: #66798A;
    border-radius: 4px;
}

QSplitter::handle {
    background-color: #E5E7EB;
}

QSplitter::handle:horizontal {
    width: 6px;
}

QSplitter::handle:vertical {
    height: 6px;
}
"""


try:
    import ifcopenshell
    import ifcopenshell.geom
except ImportError:
    ifcopenshell = None


@dataclass
class IFCParseResult:
    model: object
    schema: str
    project_name: str
    entity_count: int
    product_count: int
    spatial_count: int
    geometry_count: int
    type_counts: Counter

    def summary_lines(self):
        common_types = ", ".join(
            f"{entity_type}: {count}"
            for entity_type, count in self.type_counts.most_common(8)
        )

        return [
            f"Schema: {self.schema}",
            f"Project: {self.project_name}",
            f"Entities: {self.entity_count}",
            f"Products: {self.product_count}",
            f"Spatial elements: {self.spatial_count}",
            f"Products with representation: {self.geometry_count}",
            f"Top entity types: {common_types or 'none'}",
        ]


def unique_output_path(folder: Path, stem: str, extension: str) -> Path:
    output = folder / f"{stem}.{extension.lower()}"
    counter = 2

    while output.exists():
        output = folder / f"{stem}_{counter}.{extension.lower()}"
        counter += 1

    return output


def by_type_or_empty(model, entity_type: str):
    try:
        return model.by_type(entity_type)
    except RuntimeError:
        return []


def parse_ifc_file(input_file: Path) -> IFCParseResult:
    if ifcopenshell is None:
        raise RuntimeError("IfcOpenShell is not installed in this environment.")

    if input_file.suffix.lower() not in {".ifc", ".ifczip", ".ifcxml"}:
        raise ValueError("Only IFC input files are supported by the parser.")

    model = ifcopenshell.open(str(input_file))
    entities = list(model)
    type_counts = Counter(entity.is_a() for entity in entities)
    projects = by_type_or_empty(model, "IfcProject")
    project_name = "Unnamed project"

    if projects:
        project_name = getattr(projects[0], "Name", None) or project_name

    products = by_type_or_empty(model, "IfcProduct")
    spatial_elements = by_type_or_empty(model, "IfcSpatialElement")
    if not spatial_elements:
        spatial_elements = by_type_or_empty(model, "IfcSpatialStructureElement")
    geometry_count = sum(
        1 for product in products if getattr(product, "Representation", None)
    )

    return IFCParseResult(
        model=model,
        schema=getattr(model, "schema", "Unknown"),
        project_name=project_name,
        entity_count=len(entities),
        product_count=len(products),
        spatial_count=len(spatial_elements),
        geometry_count=geometry_count,
        type_counts=type_counts,
    )


def export_step_copy(parse_result: IFCParseResult, output_file: Path):
    parse_result.model.write(str(output_file))


def export_glb(parse_result: IFCParseResult, input_file: Path, output_file: Path):
    if parse_result.geometry_count == 0:
        raise RuntimeError("No product geometry representations were found.")

    geometry_settings = ifcopenshell.geom.settings()
    geometry_settings.set("use-world-coords", True)
    geometry_settings.set("apply-default-materials", True)
    serializer_settings = ifcopenshell.geom.serializer_settings()
    serializer_settings.set("use-element-guids", True)
    serializer_settings.set("use-element-names", True)

    serializer = ifcopenshell.geom.serializers.gltf(
        str(output_file),
        geometry_settings,
        serializer_settings,
    )
    serializer.writeHeader()

    written = 0
    for shape in ifcopenshell.geom.iterate(
        geometry_settings,
        str(input_file),
        num_threads=1,
    ):
        serializer.write(shape)
        written += 1

    serializer.finalize()

    if written == 0:
        raise RuntimeError("IfcOpenShell did not generate any mesh geometry.")


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(72)
        self.setMaximumHeight(104)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignVCenter)

        icon = QLabel("⬆")
        icon.setAlignment(Qt.AlignCenter)
        icon.setText("IFC")
        icon.setStyleSheet("font-size: 28px; font-weight: 900; color: #475569;")

        title = QLabel("Drop files or folders here")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #1F2937;")

        subtitle = QLabel("Use the buttons below for manual selection.")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []

        for url in event.mimeData().urls():
            local_path = Path(url.toLocalFile())

            if local_path.is_file():
                paths.append(str(local_path))

            elif local_path.is_dir():
                for child in local_path.iterdir():
                    if child.is_file():
                        paths.append(str(child))

        if paths:
            self.files_dropped.emit(paths)


class ConversionWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    status = Signal(str)
    stats = Signal(int, int, int)
    finished = Signal(bool)

    def __init__(self, files, output_folder, output_format):
        super().__init__()
        self.files = files
        self.output_folder = Path(output_folder)
        self.output_format = output_format.lower()
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        total = len(self.files)
        success_count = 0
        failed_count = 0
        processed_count = 0

        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.log.emit("Starting IFC parsing pipeline...")
        self.log.emit(f"Total files queued: {total}")
        self.log.emit(f"Selected export format: {self.output_format.upper()}")
        self.log.emit(f"Output directory: {self.output_folder}")
        self.log.emit("Parser engine: IfcOpenShell")
        self.log.emit("-" * 70)

        for file_index, file_path in enumerate(self.files, start=1):
            if self.cancelled:
                self.log.emit("Conversion cancelled by user.")
                self.status.emit("Cancelled")
                self.finished.emit(False)
                return

            input_file = Path(file_path)
            self.status.emit(f"Processing {file_index}/{total}: {input_file.name}")
            self.log.emit(f"[{file_index}/{total}] Loading: {input_file.name}")

            try:
                self.emit_file_progress(file_index, total, 10)
                self.log.emit("Parsing IFC model...")
                parse_result = parse_ifc_file(input_file)

                self.emit_file_progress(file_index, total, 35)
                self.log.emit("IFC parse successful.")
                for line in parse_result.summary_lines():
                    self.log.emit(f"  {line}")

                output_file = unique_output_path(
                    self.output_folder,
                    input_file.stem,
                    self.output_format,
                )

                self.emit_file_progress(file_index, total, 55)
                self.log.emit(f"Preparing {self.output_format.upper()} export...")

                if self.output_format == "stp":
                    export_step_copy(parse_result, output_file)
                elif self.output_format == "glb":
                    export_glb(parse_result, input_file, output_file)
                else:
                    raise ValueError(f"Unsupported export format: {self.output_format}")

                self.emit_file_progress(file_index, total, 100)
                success_count += 1
                self.log.emit(f"Success: created {output_file.name}")

            except Exception as error:
                failed_count += 1
                self.log.emit(f"Failed: {input_file.name}")
                self.log.emit(f"Reason: {error}")

            processed_count += 1
            self.stats.emit(processed_count, success_count, failed_count)
            self.log.emit("-" * 70)

        self.progress.emit(100)
        self.status.emit("Finished")
        self.log.emit("IFC parsing pipeline completed.")
        self.finished.emit(True)

    def emit_file_progress(self, file_index, total, file_percent):
        overall = int(((file_index - 1 + file_percent / 100) / total) * 100)
        self.progress.emit(overall)


class IFCConverterDemo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IFC Converter")
        self.resize(980, 620)
        self.setMinimumSize(700, 520)

        self.selected_files = []
        self.output_folder = None
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0

        self.thread = None
        self.worker = None
        self.body_splitter = None
        self.content_widget = None

        self.setup_ui()

    def setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.create_content())

        root_layout.addWidget(scroll)
        self.update_responsive_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_layout()

    def update_responsive_layout(self):
        if not self.body_splitter:
            return

        if self.width() < 820:
            if self.body_splitter.orientation() != Qt.Vertical:
                self.body_splitter.setOrientation(Qt.Vertical)
                self.body_splitter.setSizes([360, 430])
            if self.content_widget:
                self.content_widget.setMinimumHeight(860)
                self.content_widget.setMaximumHeight(16777215)
        else:
            if self.body_splitter.orientation() != Qt.Horizontal:
                self.body_splitter.setOrientation(Qt.Horizontal)
                self.body_splitter.setSizes([560, 420])
            if self.content_widget:
                self.content_widget.setMinimumHeight(0)
                self.content_widget.setMaximumHeight(max(520, self.height()))

    def create_content(self):
        content = QWidget()
        self.content_widget = content

        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        hero = self.create_hero()

        left_panel = QWidget()
        left_col = QVBoxLayout(left_panel)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)

        right_panel = QWidget()
        right_col = QVBoxLayout(right_panel)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)

        left_col.addWidget(self.create_upload_card(), 0)
        left_col.addWidget(self.create_file_list_card(), 1)

        right_col.addWidget(self.create_export_card(), 0)
        right_col.addWidget(self.create_progress_card(), 0)
        right_col.addWidget(self.create_logs_card(), 1)

        self.body_splitter = QSplitter(Qt.Horizontal)
        self.body_splitter.setChildrenCollapsible(False)
        self.body_splitter.addWidget(left_panel)
        self.body_splitter.addWidget(right_panel)
        self.body_splitter.setStretchFactor(0, 6)
        self.body_splitter.setStretchFactor(1, 5)
        self.body_splitter.setSizes([560, 420])

        layout.addWidget(hero)
        layout.addWidget(self.body_splitter, 1)

        return content

    def create_hero(self):
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero.setMinimumHeight(48)
        hero.setMaximumHeight(66)

        layout = QHBoxLayout(hero)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("IFC Converter")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Parse IFC files with IfcOpenShell and export GLB or STEP targets."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        layout.addLayout(title_box, 1)

        return hero

    def create_upload_card(self):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("Input Selection")
        header.setObjectName("SectionTitle")

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("PrimaryButton")
        browse_btn.clicked.connect(self.browse_files)
        browse_btn.setMinimumHeight(32)
        browse_btn.setToolTip("Select one or more files of any type")

        self.input_buttons = [browse_btn]

        buttons.addWidget(browse_btn)

        layout.addWidget(header)
        layout.addWidget(self.drop_area)
        layout.addLayout(buttons)

        return card

    def create_file_list_card(self):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_row = QHBoxLayout()

        title = QLabel("Selected Files")
        title.setObjectName("SectionTitle")

        self.file_count_label = QLabel("0 files")
        self.file_count_label.setObjectName("Muted")

        self.clear_queue_btn = QPushButton("Clear")
        self.clear_queue_btn.setObjectName("DangerButton")
        self.clear_queue_btn.clicked.connect(self.clear_files)
        self.clear_queue_btn.setMinimumHeight(28)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.file_count_label)
        header_row.addWidget(self.clear_queue_btn)

        self.file_list = QListWidget()
        self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.file_list.setMinimumHeight(120)
        self.file_list.itemChanged.connect(self.update_file_count)

        layout.addLayout(header_row)
        layout.addWidget(self.file_list)

        return card

    def create_export_card(self):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Export Settings")
        title.setObjectName("SectionTitle")

        self.format_group = QButtonGroup(self)
        self.format_group.setExclusive(True)
        self.format_buttons = {}

        format_grid = QGridLayout()
        format_grid.setContentsMargins(0, 0, 0, 0)
        format_grid.setHorizontalSpacing(8)
        format_grid.setVerticalSpacing(0)

        formats = [
            ("GLB", "3D / web viewer"),
            ("STP", "CAD export"),
        ]

        for index, (fmt, description) in enumerate(formats):
            btn = QPushButton(fmt)
            btn.setCheckable(True)
            btn.setToolTip(description)
            btn.setObjectName("FormatOptionButton")
            btn.setProperty("format", fmt)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            self.format_group.addButton(btn)
            self.format_buttons[fmt] = btn

            row = index // 2
            col = index % 2
            format_grid.addWidget(btn, row, col)

        format_grid.setColumnStretch(0, 1)
        format_grid.setColumnStretch(1, 1)
        self.format_buttons["GLB"].setChecked(True)

        output_btn = QPushButton("Output Folder")
        output_btn.setObjectName("SecondaryButton")
        output_btn.clicked.connect(self.choose_output_folder)
        output_btn.setFixedHeight(32)

        self.output_label = QLabel("No output folder selected")
        self.output_label.setObjectName("SmallMuted")
        self.output_label.setWordWrap(True)
        self.output_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.output_label.setMinimumHeight(28)
        self.output_label.setMaximumHeight(42)

        self.output_buttons = [output_btn]

        layout.addWidget(title)
        layout.addLayout(format_grid)
        layout.addSpacing(4)
        layout.addWidget(output_btn)
        layout.addWidget(self.output_label)

        return card

    def create_progress_card(self):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Conversion Status")
        title.setObjectName("SectionTitle")

        self.status_label = QLabel("Ready to start")
        self.status_label.setObjectName("Muted")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.stats_label = QLabel("Processed 0 | Success 0 | Failed 0")
        self.stats_label.setObjectName("SmallMuted")
        self.stats_label.setWordWrap(True)
        self.stats_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self.start_conversion)
        self.start_btn.setMinimumHeight(34)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DangerButton")
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumHeight(34)

        actions.addWidget(self.start_btn, 1)
        actions.addWidget(self.cancel_btn, 1)

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(actions)

        return card

    def create_logs_card(self):
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("Live Logs")
        title.setObjectName("SectionTitle")

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logs.setMinimumHeight(90)

        layout.addWidget(title)
        layout.addWidget(self.logs, 1)

        return card

    def browse_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select One or More IFC Files",
            "",
            "IFC Files (*.ifc *.ifczip *.ifcxml);;All Files (*.*)"
        )

        if file_paths:
            self.add_files(file_paths)

    def add_files(self, files):
        added = 0

        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)

                path = Path(file)
                extension = path.suffix if path.suffix else "no extension"
                item = QListWidgetItem(f"{path.name}    |    {extension}")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setToolTip(str(path))
                self.file_list.addItem(item)
                added += 1

        self.update_file_count()

        if added > 0:
            self.log(f"Added {added} file(s). Total queued: {len(self.selected_files)}")
        else:
            self.log("No new files added. Duplicates were skipped.")

    def clear_files(self):
        self.selected_files = []
        self.file_list.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to start")
        self.update_file_count()
        self.update_stats(0, 0, 0)
        self.log("Queue cleared.")

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")

        if folder:
            self.output_folder = folder
            self.output_label.setText(folder)
            self.log(f"Output folder selected: {folder}")

    def get_selected_format(self):
        checked_button = self.format_group.checkedButton()

        if checked_button:
            return checked_button.property("format")

        return "GLB"

    def get_included_files(self):
        included_files = []

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)

            if item.checkState() == Qt.CheckState.Checked:
                included_files.append(item.toolTip())

        return included_files

    def start_conversion(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Missing files", "Please add at least one file.")
            return

        included_files = self.get_included_files()

        if not included_files:
            QMessageBox.warning(
                self,
                "No files selected",
                "Select at least one queued file to convert."
            )
            return

        if not self.output_folder:
            QMessageBox.warning(
                self,
                "Missing output folder",
                "Please choose an output folder."
            )
            return

        self.logs.clear()
        self.progress_bar.setValue(0)
        self.update_stats(0, 0, 0)

        output_format = self.get_selected_format()

        self.set_running_state(True)

        self.thread = QThread()
        self.worker = ConversionWorker(
            included_files,
            self.output_folder,
            output_format
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.log)
        self.worker.status.connect(self.status_label.setText)
        self.worker.stats.connect(self.update_stats)
        self.worker.finished.connect(self.on_conversion_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def cancel_conversion(self):
        if self.worker:
            self.worker.cancel()
            self.log("Cancel requested...")

    def on_conversion_finished(self, completed):
        self.set_running_state(False)

        if completed:
            self.status_label.setText("Finished")
            self.log("Worker finished successfully.")
            QTimer.singleShot(0, self.show_completion_dialog)
        else:
            self.status_label.setText("Cancelled")
            self.log("Worker stopped before completion.")

    def show_completion_dialog(self):
        QMessageBox.information(
            self,
            "Conversion Complete",
            (
                "IFC processing completed.\n\n"
                f"Processed: {self.processed_count}\n"
                f"Created: {self.success_count}\n"
                f"Failed: {self.failed_count}\n\n"
                f"Output folder:\n{self.output_folder}"
            )
        )
        self.reset_app_state()

    def reset_app_state(self):
        self.selected_files = []
        self.output_folder = None
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.worker = None
        self.thread = None

        self.file_list.clear()
        self.output_label.setText("No output folder selected")
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to start")
        self.update_stats(0, 0, 0)
        self.update_file_count()
        self.logs.clear()

        if "GLB" in self.format_buttons:
            self.format_buttons["GLB"].setChecked(True)

    def set_running_state(self, running):
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        self.file_list.setEnabled(not running)

        for button in self.input_buttons + self.output_buttons + [self.clear_queue_btn]:
            button.setEnabled(not running)

        for button in self.format_buttons.values():
            button.setEnabled(not running)

    def update_file_count(self, *args):
        count = len(self.selected_files)
        included = len(self.get_included_files()) if hasattr(self, "file_list") else 0
        self.file_count_label.setText(
            f"{included} selected / {count} file{'s' if count != 1 else ''}"
        )

    def update_stats(self, processed, success, failed):
        self.processed_count = processed
        self.success_count = success
        self.failed_count = failed
        self.stats_label.setText(
            f"Processed {processed} | Success {success} | Failed {failed}"
        )

    def log(self, message):
        self.logs.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI"))

    window = IFCConverterDemo()
    window.show()

    sys.exit(app.exec())
