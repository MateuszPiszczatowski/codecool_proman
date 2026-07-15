import {dataHandler} from "../data/dataHandler.js";
import {htmlFactory, htmlTemplates} from "../view/htmlFactory.js";
import {domManager} from "../view/domManager.js";
import {showMessage} from "../view/utils.js";
import {dragManager} from './dragHandler.js';


export let cardsManager = {
    loadCards: async function (boardId, statusId) {
        const cards = await dataHandler.getCardsByBoardId(boardId);
        for (let card of cards) {
            if (card.status_id !== parseInt(statusId, 10) || card.board_id !== parseInt(boardId, 10))
                continue;
            if (card.body == null) {
                card.body = "";
            }
            const cardBuilder = htmlFactory(htmlTemplates.card);
            const content = cardBuilder(card);
            domManager.addChild(
                `.board__card-container[data-board-id="${boardId}"][data-status-id="${statusId}"]`,
                content
            );
            domManager.addEventListener(
                `input[data-card-id="${card.id}"]`,
                "change",
                updateHandler
            );
            domManager.addEventListener(
                `textarea[data-card-id="${card.id}"]`,
                "change",
                textareaUpdateHandler
            );
            domManager.addEventListener(
                `.button-delete[data-card-id="${card.id}"]`,
                "click",
                deleteHandler
            );
            const inputs = document.querySelectorAll("input");
            const textareas = document.querySelectorAll("textarea");
            const fields = [...inputs, ...textareas];
            fields.forEach((field) => {
                field.addEventListener("focus", () => {
                    field.setSelectionRange(-1, -1);
                });
            });
        }
    },
    addCardEvent: async (e) => {
        const button = e.currentTarget;
        button.toggleAttribute("disabled");
        const board = button.parentNode.parentNode;
        if (!isBoardOpen(board)) {
            handleClosedBoard(button);
            return;
        }
        const boardId = board.querySelector(".board__title-input").dataset
            .boardId;
        const firstStatus = board.querySelector(".board__card-container");
        if (firstStatus) {
            await addCard(button, boardId, firstStatus);
        } else {
            showMessage("There must be at least one status to add a card");
            button.toggleAttribute("disabled");
        }
    },
};

const isBoardOpen = (board) => {
    const accordionBody = board.querySelector(".accordion-collapse");
    if (!accordionBody) {
        return false;
    }
    return accordionBody.classList.contains("show");
};

const handleClosedBoard = (button) => {
    showMessage("Board must be open to add cards");
    button.toggleAttribute("disabled");
};

const addCard = async (button, boardId, firstStatus) => {
    const {dom: cardDOMNode, data: cardData} = addCardToDOM(
        boardId,
        firstStatus
    );
    const addCardResponse = await addCardToDB(cardData);
    if (addCardResponse["success"]) {
        updateDOMCard(button, cardDOMNode, addCardResponse);
    } else {
        showMessage("There was an error, deleting new card...", "error");
        cardDOMNode.parentNode.removeChild(cardDOMNode);
        button.toggleAttribute("disabled");
    }
};

const updateDOMCard = (button, cardDOMNode, addCardResponse) => {
    cardDOMNode.toggleAttribute("disabled");
    button.toggleAttribute("disabled");
    cardDOMNode.dataset.cardId = addCardResponse["card"]["id"];
    cardDOMNode.dataset.cardOrder = addCardResponse["card"]["card_order"];
    const cardInputNode = cardDOMNode.querySelector("input");
    cardInputNode.dataset.cardId = addCardResponse["card"]["id"];
    cardInputNode.dataset.cardOrder = addCardResponse["card"]["card_order"];
    const deleteButton = cardDOMNode.querySelector(".button-delete");
    deleteButton.dataset.cardId = addCardResponse["card"]["id"];
    deleteButton.addEventListener("click", deleteHandler);
    const inputs = cardDOMNode.querySelectorAll("input");
    const textareas = cardDOMNode.querySelectorAll("textarea");
    const fields = [...inputs, ...textareas];
    fields.forEach((field) => {
        field.addEventListener("focus", () => {
            field.setSelectionRange(-1, -1);
        });
    });
    dragManager.handleNewElement(cardDOMNode,'card');
    const cardInput = cardDOMNode.querySelector(".board__card-title");
    cardInput.addEventListener("change", updateHandler);
    const cardTextarea = cardDOMNode.querySelector(".board__card-text");
    cardTextarea.dataset.cardId=addCardResponse["card"]["id"];
    cardTextarea.dataset.boardId=addCardResponse["card"]["board_id"];
    cardTextarea.addEventListener("change",textareaUpdateHandler);
};

const addCardToDB = async (card) => {
    return await dataHandler.createNewCard(card);
};

const addCardToDOM = (boardId, firstStatus) => {
    const firstStatusId = firstStatus.dataset.statusId;
    const card = {
        title: "New card",
        status_id: firstStatusId,
        body: "",
        board_id: boardId,
        archived: false,
    };
    const cardHMTLContent = htmlFactory(htmlTemplates.card)(card);
    firstStatus.insertAdjacentHTML("beforeend", cardHMTLContent);
    const cardDOMNode = firstStatus.querySelector(".card:last-child");
    cardDOMNode.toggleAttribute("disabled");
    return {dom: cardDOMNode, data: card};
};

async function updateHandler() {
    if(!this.value.trim()){
        return;
    }
    const boardId = parseInt(this.dataset.boardId, 10);
    const cardId = parseInt(this.dataset.cardId, 10);
    await dataHandler.updateCard(boardId, cardId, {
        title: this.value,
        body: this.parentElement.nextElementSibling.value,
    });
}

async function textareaUpdateHandler() {
    const boardId = parseInt(this.dataset.boardId, 10);
    const cardId = parseInt(this.dataset.cardId, 10);
    const card = this.closest(".card");
    const title = card.querySelector(".board__card-title").value;
    if(!this.value.trim()){
        return;
    }
    await dataHandler.updateCard(boardId, cardId, {
        title: title,
        body: this.value,
    });
}

export const cardsModal = () => {
    const cardsModalEvent = (e) =>{
        if (e.target.closest("button") || e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
            return;
        }
        const card = e.target.closest(".card");
        if (!card){
            console.log("Couldn't get the card for DOM element: ", e.target)
            return;
        }
        if (card.hasAttribute("disabled")) {
            return;
        }
        const cardTitle =
            card.querySelector(".board__card-title").value;
        const cardText =
            card.querySelector(".board__card-text").value;
        const modalElement = document.querySelector("#card-modal");
        document.querySelector("#card-modal__input").value =
            cardTitle;
        document.querySelector("#card-modal__textarea").value =
            cardText;
        // noinspection JSUnresolvedReference
        new bootstrap.Modal(modalElement).show();

    }
    const boardsAccordion = document.querySelector("#boardsAccordion");
    boardsAccordion.addEventListener("dblclick", cardsModalEvent);
};

async function deleteHandler() {
    await dataHandler.deleteCard(
        parseInt(this.dataset.boardId, 10),
        parseInt(this.dataset.cardId, 10)
    );
    this.closest('.card').remove();
}
