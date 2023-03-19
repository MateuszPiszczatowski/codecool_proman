import { dataHandler } from "../data/dataHandler.js";
import { htmlFactory, htmlTemplates } from "../view/htmlFactory.js";
import { domManager } from "../view/domManager.js";
import { cardsManager } from "./cardsManager.js";
import { showMessage } from "../view/utils.js";
import { dragManager } from "./dragHandler.js";

export let statusesManager = {
    loadStatuses: async function (boardId) {
        const statuses = await dataHandler.getStatusesByBoardId(boardId);
        for (let status of statuses) {
            const statusBuilder = htmlFactory(htmlTemplates.status);
            const content = statusBuilder(status, boardId);
            domManager.addChild(
                `.board__body[data-board-id="${boardId}"]`,
                content
            );
            domManager.addEventListener(
                `input[data-status-id="${status.id}"]`,
                "change",
                updateHandler
            );
            domManager.addEventListener(
                `.button-delete[data-status-id="${status.id}"]`,
                "click",
                deleteHandler
            );
            await cardsManager.loadCards(boardId, status.id);
        }
        const addStatusInput = htmlFactory(htmlTemplates.addStatus)(boardId);
        domManager.addChild(
            `.board__body[data-board-id="${boardId}"]`,
            addStatusInput
        );
        const addStatusDOMElem = document.querySelector(
            `.board__status-input--new[data-board-id="${boardId}"]`
        );
        addStatusDOMElem.addEventListener("blur", handleAddStatus);
        addStatusDOMElem.addEventListener("keydown", handleAddStatus);
    },
    postStatus: async function (payload) {
        return await dataHandler.createNewStatus(payload);
    },
};

const handleAddStatus = async (e) => {
    const boardId = e.currentTarget.dataset["boardId"];
    const inputNode = document.querySelector(
        `input.board__status-input--new[data-board-id="${boardId}"]`
    );
    const newStatusTitle = inputNode.value;
    if (newStatusTitle !== "") {
        if (e.type !== "keydown" || e.key === "Enter") {
            inputNode.value = "";
            inputNode.toggleAttribute("disabled");
            const statusObject = await createTemporaryStatus(
                boardId,
                newStatusTitle,
                inputNode.parentNode.parentNode
            );
            try {
                await addStatusToDB(statusObject, newStatusTitle, boardId);
            } catch (error) {
                handleAddStatusToDBError(error, statusObject);
            }
            inputNode.toggleAttribute("disabled");
        }
    }
};

const handleAddStatusToDBError = (error, statusObject) => {
    showMessage("There was an error: " + error.toString(), error);
    statusObject.renderedStatus.parentElement.remove();
};

const addStatusToDB = async (statusObject, newStatusTitle, boardId) => {
    const statusResponse = await statusesManager.postStatus({
        title: newStatusTitle,
        boardId: boardId,
    });
    for (let key in statusObject) {
        statusObject[key].dataset.statusId = statusResponse.id;
    }
    statusObject.renderedInput.toggleAttribute("disabled");
    statusObject.renderedInput.addEventListener("change", updateHandler);
    statusObject.renderedStatus
        .querySelector(".button-delete")
        .addEventListener("click", deleteHandler);
    dragManager.handleNewElement(statusObject.renderedStatus, "statusDrag");
    dragManager.handleNewElement(
        statusObject.renderedCardContainer,
        "statusDrop"
    );
};

const createTemporaryStatus = async (boardId, title, lastElem) => {
    const temporaryStatusID = `B-${boardId}-newStatus`;
    const statusBuilder = htmlFactory(htmlTemplates.status);
    const content = statusBuilder({
        title: title,
        id: temporaryStatusID,
        board_id: boardId,
    });
    lastElem.insertAdjacentHTML("beforebegin", content);
    const statusObject = {
        renderedInput: document.querySelector(
            `input[data-status-id=${temporaryStatusID}]`
        ),
        renderedStatus: document.querySelector(
            `div[data-status-id=${temporaryStatusID}]`
        ),
        renderedCardContainer: document.querySelector(
            `div[data-status-id=${temporaryStatusID}].card-droppable`
        ),
        renderdDeleteButton: document.querySelector(
            `button[data-status-id=${temporaryStatusID}].button-delete`
        ),
    };
    statusObject.renderedInput.toggleAttribute("disabled");
    return statusObject;
};

function showHideButtonHandler(clickEvent) {
    const statusId = clickEvent.target.dataset.statusId;
    cardsManager.loadCards(boardId, statusId);
}

function updateHandler() {
    let statusId = parseInt(this.dataset.statusId);
    let boardId = parseInt(this.dataset.boardId);
    dataHandler.updateStatus(boardId, statusId, {
        title: this.value,
    });
}

async function deleteHandler() {
    await dataHandler.deleteStatus(
        parseInt(this.dataset.boardId),
        parseInt(this.dataset.statusId)
    );
    this.parentElement.parentElement.remove();
}
