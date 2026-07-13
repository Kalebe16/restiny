from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QAbstractItemView,
    QStyle,
    QStyledItemDelegate,
    QTreeWidget,
    QTreeWidgetItem,
)

from restiny.entities import Folder, Request

METHOD_COLORS = {
    'GET': '#7FD98A',
    'POST': '#7EC8E3',
    'PUT': '#FFCB77',
    'DELETE': '#F28B82',
    'PATCH': '#C7A6FF',
    'HEAD': '#CFCFCF',
    'OPTIONS': '#8FD3E8',
    'CONNECT': '#D9B38C',
    'TRACE': '#F6A6C9',
}


class RichTextDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        text = index.data()
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setHtml(text)

        painter.save()

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())

        painter.translate(option.rect.topLeft())
        doc.setTextWidth(option.rect.width())
        doc.drawContents(painter)

        painter.restore()


class CollectionsTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests_by_id: dict[int, QTreeWidgetItem] = {}
        self.folders_by_id: dict[int, QTreeWidgetItem] = {}

        self.setTextElideMode(Qt.ElideNone)
        self.setItemDelegate(RichTextDelegate())

    def add_folder(self, folder: Folder, parent_item) -> None:
        item = QTreeWidgetItem([folder.name])
        item.setData(
            0,
            Qt.UserRole,
            {'id': folder.id, 'type': 'folder', 'name': folder.name},
        )
        self.folders_by_id[folder.id] = item
        if parent_item:
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)
        return item

    def add_request(self, request: Request, parent_item=None) -> None:
        color = METHOD_COLORS.get(request.method.upper())
        item = QTreeWidgetItem(
            [
                f"<span style='color:{color}'>{request.method}</span> {request.name}"
            ]
        )
        item.setData(
            0,
            Qt.UserRole,
            {
                'id': request.id,
                'type': 'request',
                'method': request.method,
                'name': request.name,
            },
        )
        self.requests_by_id[request.id] = item

        if parent_item:
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)

        return item

    def update_folder(self, folder: Folder) -> None:
        item = self.folders_by_id.get(folder.id)
        item.setText(0, folder.name)
        item.setData(
            0,
            Qt.UserRole,
            {'id': folder.id, 'type': 'folder', 'name': folder.name},
        )

    def update_request(self, request: Request) -> None:
        item = self.requests_by_id.get(request.id)
        color = METHOD_COLORS.get(request.method.upper())
        item.setText(
            0,
            f"<span style='color:{color}'>{request.method}</span> {request.name}",
        )
        item.setData(
            0,
            Qt.UserRole,
            {
                'id': request.id,
                'type': 'request',
                'method': request.method,
                'name': request.name,
            },
        )

    def delete_folder_by_id(self, folder_id: int) -> None:
        self.setSelectionMode(QAbstractItemView.NoSelection)
        item = self.folders_by_id.pop(folder_id)
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)

        del item
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def delete_request_by_id(self, request_id: int) -> None:
        self.setSelectionMode(QAbstractItemView.NoSelection)
        item = self.requests_by_id.pop(request_id)
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)

        del item
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def move_request(self, request: Request, new_folder_id: int) -> None:
        item = self.requests_by_id[request.id]
        parent = item.parent()

        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)

        parent_item = None
        if new_folder_id is not None:
            parent_item = self.folders_by_id[new_folder_id]
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)

        self.setCurrentItem(item)
        item.setSelected(True)

    def move_folder(self, folder: Folder, new_parent_id: int | None) -> None:
        item = self.folders_by_id[folder.id]

        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)

        if new_parent_id is not None:
            parent_item = self.folders_by_id[new_parent_id]
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)

        self.setCurrentItem(item)
        item.setSelected(True)

    def currentItemData(self) -> dict | None:
        item = self.currentItem()
        if not item:
            return None
        return item.data(0, Qt.UserRole)
