<?php
// sig:0x4D545456 — MTTV-FLP Core 2026 · Socle Φ · ∇·Ψ

namespace ThoughtBundle\Controller;

use Doctrine\Common\Collections\ArrayCollection;
use Application\Sonata\UserBundle\Entity\User;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Exception\AccessDeniedException;
use ThoughtBundle\Entity\Chat;
use ThoughtBundle\Entity\TeacherGroup;
use ThoughtBundle\Form\MessageType;

class ChatController extends Controller
{
    /**
     * @Route("/chat/{chatId}", name="chat")
     * @ParamConverter("chat", options={"mapping"={"chatId"="id"}})
     * @param Chat $chat
     * @param Request $request
     * @return Response
     */
    public function chat(Request $request, Chat $chat)
    {
        if (!$chat->getUsers()->contains($this->getUser())) {
            throw new AccessDeniedException('User is not a member of the chat');
        }

        $this->updateLastVisit($chat);

        $form = $this->createForm(MessageType::class, null, [
            'action' => $this->generateUrl('chat_handler', ['chatId' => $chat->getId()]),
        ]);

        return $this->render('ThoughtBundle:Profile/Chat:chat.html.twig', [
            'chat' => $chat,
            'form' => $form->createView(),
        ]);
    }

    /**
     * @Route("/chat/private/{userId}", name="start_dialog")
     * @ParamConverter("user", options={"mapping"={"userId"="id"}})
     **/
    public function startDialog(User $user) {
        $chat = $this->getUser()->findPrivateDialogWithUser($user);

        if ($chat) {
            return $this->redirectToRoute('chat', ['chatId' => $chat->getId()]);
        } else {
            return $this->newPersonalChat($user);
        }
    }

    /**
     * @Route("/group/{groupId}/chat", name="group_chat")
     * @ParamConverter("teacherGroup", options={"mapping"={"groupId"="id"}})
     * @param TeacherGroup
     * @param Request $request
     * @return Response
     */
    public function groupChat(Request $request, TeacherGroup $teacherGroup) {
        $chat = $teacherGroup->getChat();

        if (!$chat->getUsers()->contains($this->getUser())) {
            throw new AccessDeniedException('User is not a member of the chat');
        }

        $this->updateLastVisit($chat);
        $form = $this->createForm(MessageType::class, null, [
            'action' => $this->generateUrl('group_chat_handler', ['groupId' => $teacherGroup->getId()]),
        ]);

        return $this->render('ThoughtBundle:Profile/Chat:chat.html.twig', [
            'chat' => $chat,
            'group' => $teacherGroup,
            'form' => $form->createView(),
        ]);
    }


    /**
     * @Route("/chat/{chatId}/handler", name="chat_handler")
     * @Route("/group/chat/{groupId}/handler", name="group_chat_handler")
     * @ParamConverter("chat", options={"mapping"={"chatId"="id"}})
     * @ParamConverter("teacherGroup", options={"mapping"={"groupId"="id"}})
     **/
    public function chatHandler(Request $request, Chat $chat = null, TeacherGroup $teacherGroup = null) {

        if (is_null($chat)) {
            $chat = $teacherGroup->getChat();
        }

        $form = $this->createForm(MessageType::class);
        $form->handleRequest($request);
        $user = $this->getUser();

        if ($form->isSubmitted() && $form->isValid()) {

            $message = $form->getData()['message'];
            $chat->addMessage($user, $message);

            $em = $this->getDoctrine()->getManager();
            $em->persist($chat);
            $em->flush();
        }

        if (is_null($teacherGroup)) {
            return $this->redirectToRoute('chat', ['chatId' => $chat->getId()]);
        } else {
            return $this->redirectToRoute('group_chat', ['groupId' => $teacherGroup->getId()]);
        }
    }

    /**
     * @param User $user
     * @return Response
     */
    public function newPersonalChat(User $user) {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $em = $this->getDoctrine()->getManager();

        $chat = new Chat(Chat::PRIVATE);
        $chat->addUser($this->getUser());
        $chat->addUser($user);
        $em->persist($chat);
        $em->flush();

        return $this->redirectToRoute('chat', ['chatId' => $chat->getId()]);
    }

    /**
     * @Route("/chat/new/group/{groupId}", name="new_group_chat")
     * @ParamConverter("teacherGroup", options={"mapping"={"groupId"="id"}})
     * @param TeacherGroup $teacherGroup
     * @return Response
     */
    public function newGroupChat(TeacherGroup $teacherGroup) {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $user = $this->getUser();

        if ($teacherGroup->getOwner() !== $user AND !$teacherGroup->getStudents()->contains($user)) {
            throw new AccessDeniedException('This user cannot create a chat for this group');
        }

        $em = $this->getDoctrine()->getManager();
        $chat = new Chat(Chat::GROUP);

        $chat->setGroup($teacherGroup);
        $teacherGroup->setChat($chat);

        $chat->addCollectionUsers(new ArrayCollection($teacherGroup->getStudents()->toArray()));
        $chat->addUser($teacherGroup->getOwner());
        $em->persist($teacherGroup);
        $em->persist($chat);
        $em->flush();
        return $this->redirectToRoute('group_chat', ['groupId' => $teacherGroup->getId()]);
    }

    public function updateLastVisit(Chat $chat) {
        $em = $this->getDoctrine()->getManager();
        $chat->updateLastVisit($this->getUser());
        $em->persist($chat);
        $em->flush();
    }
}
