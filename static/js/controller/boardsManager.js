import {dataHandler} from "../data/dataHandler.js";
import {htmlFactory, htmlTemplates} from "../view/htmlFactory.js";
import {domManager} from "../view/domManager.js";
import {statusesManager} from "./statusesManager.js";
import {cardsManager} from "./cardsManager.js";
import { dragManager } from "./dragHandler.js";
import {showMessage, toggleLoadingCursor} from "../view/utils.js";

export let boardsManager = {
    loadBoards: async function () {
        document.querySelector('#boardsAccordion').innerHTML='';
        const boards = await dataHandler.getBoards();
        for (let board of boards) {
            const boardBuilder = htmlFactory(htmlTemplates.board);
            const content = boardBuilder(board);
            domManager.addChild("#boardsAccordion", content);
            domManager.addEventListener(
                `.accordion-button[data-board-id="${board.id}"]`,
                "click",
                showHideButtonHandler
            );
            domManager.addEventListener(
                `.board__add-card-button[data-board-id="${board.id}"]`,
                "click",
                cardsManager.addCardEvent
            );

            domManager.addEventListener(
                `input[data-board-id="${board.id}"]`,
                "change",
                updateHandler
            );
            domManager.addEventListener(
                `.button-delete[data-board-id="${board.id}"]`,
                "click",
                deleteHandler
            );
        }
        domManager.addEventListener('#new-board-form', 'submit', addHandler);
        domManager.addEventListener('#refresh-button', 'click', this.loadBoards);
    },
};


async function addHandler(e) {
    e.preventDefault();
    toggleLoadingCursor()
    const form = e.target;
    const boardName = form.elements['board-name'].value;
    const isPrivate = form.elements['board-private'].checked;
    const payload = {'title': boardName, 'is_private': isPrivate};
    const result = await dataHandler.createNewBoard(payload);
    if (result['success']) {
        showMessage(result['message'], 'success');
    } else {
        showMessage(result['message'], 'error');
    }
    toggleLoadingCursor();
    await boardsManager.loadBoards();
}


async function showHideButtonHandler(clickEvent) {
    const boardId = clickEvent.target.dataset.boardId;
    const boardBody = document.querySelector(
        `.row.board__body[data-board-id="${boardId}"]`
    );
    if (boardBody.children.length == 0) {
        await statusesManager.loadStatuses(boardId);
        dragManager.initDragElements();
    }
}

async function updateHandler() {
    dataHandler.updateBoard({
        title: this.value,
        is_private: this.dataset.boardPrivate,
        id: parseInt(this.dataset.boardId),
    });
}

async function deleteHandler() {
    await dataHandler.deleteBoard(parseInt(this.dataset.boardId));
    this.parentElement.parentElement.remove();
}
