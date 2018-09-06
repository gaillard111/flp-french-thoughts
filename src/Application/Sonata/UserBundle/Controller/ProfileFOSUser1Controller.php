<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Entity\Dialog;
use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Type\MessageType;
use Application\Sonata\UserBundle\Form\Type\ProfileInfoType;
use Application\Sonata\UserBundle\Repository\FriendshipRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Component\Translation\Loader\ArrayLoader;
use Symfony\Component\Translation\Translator;

/**
 * Class ProfileFOSUser1Controller
 * @package Application\Sonata\UserBundle\Controller
 */
class ProfileFOSUser1Controller extends \Sonata\UserBundle\Controller\ProfileFOSUser1Controller
{
    /**
     * @Route("/profile-info", name="sonata_user_edit_profile_info")
     * @param Request $request
     * @return Response
     * @throws \Doctrine\ORM\OptimisticLockException
     */
    public function editProfileInfoAction(Request $request)
    {
        $user = $this->getUser();

        $form = $this->createForm(new ProfileInfoType(), $user);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {

            if ($form->isValid()) {

                $entityManager = $this->container->get('doctrine.orm.entity_manager');
                $entityManager->persist($user);
                $entityManager->flush();

            } else {

                $errors = $this->getErrorMessages($form);
                $messages = $this->errorMessages($errors);
                $this->setFlash('sonata_user_error', $messages);
            }
            return $this->redirectToRoute('sonata_user_profile_edit');
        }
        return $this->render('@ApplicationSonataUser/Profile/Form/edit_profile_info.html.twig', [
            'form'  => $form->createView(),
        ]);
    }

    /**
     * @Route("/friends", name="friends")
     */
    public function friendsAction()
    {
        $entityManager  = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship');
        $friendRequests = $entityManager->getCountFriendRequests($this->getUser());
        $friends        = $entityManager->getCountFriends($this->getUser());
        return $this->render('@ApplicationSonataUser/Profile/friends.html.twig', [
            'countReq'      => $friendRequests,
            'countFriends'  => $friends
        ]);
    }

    /**
     * @Route("/dialogs", name="dialog_list")
     */
    public function userDialogsAction()
    {

        $user = $this->getUser();

        $dialogs = $user->getDialogs();

        foreach ($dialogs as $key => $dialog) {
            /** @var Dialog $dialog */
            $lastMessages[$key] = $this->getDoctrine()->getRepository(Message::class)->getLastMessageFromDialog($dialog->getId());
        }
        return $this->render('@ApplicationSonataUser/Profile/dialogs.html.twig', [
            'dialogs'      => $dialogs,
            'lastMessages' => $lastMessages
        ]);
    }

    /**
     * @Route("/dialog/{dialogId}", name="dialog")
     */
    public function dialogAction($dialogId, Request $request)
    {
        $em = $this->getDoctrine()->getEntityManager();

        $dialog = $em->getRepository('ApplicationSonataUserBundle:Dialog')->find($dialogId);

        if ($dialog) {

            $newMessages = $em->getRepository(Message::class)->getNewMessagesFromDialog($dialogId, $this->getUser()->getId());
            if ($newMessages) {
                foreach ($newMessages as $newMessage) {

                    /** @var Message $newMessage */
                    $newMessage->setIsViewed(true);
                    $em->persist($newMessage);
                    $em->flush();
                }
            }

            $message = new Message();
            $message->setSender($this->getUser());
            $message->setDialog($dialog);


            $form = $this->createForm(MessageType::class, $message);
            $form->handleRequest($request);


            if ($form->isSubmitted() && $form->isValid()) {

                $message = $form->getData();
                $em->persist($message);
                $em->persist($dialog);
                $em->flush();
                $em->clear(Dialog::class);
                $em->clear(Message::class);


                return $this->redirectToRoute('dialog', [
                    'dialogId'  =>  $dialogId,
                ]);
            }

            $messages = $em->getRepository(Message::class)->getMessagesFromDialog($dialogId);

            $dialogUsers = $dialog->getUsers();

            $paginator  = $this->get('knp_paginator');
            $pagination = $paginator->paginate(
                $messages,
                $request->query->getInt('page', 1),
                10
            );

            foreach ($dialogUsers as $user) {
                if ($user == $this->getUser()) {
                    return $this->render('ApplicationSonataUserBundle:Profile:dialog.html.twig', [
                        'messages'  => $pagination,
                        'dialog'    => $dialog,
//                'receiver'  => $reciever,
                        'form'  => $form->createView()
                    ]);
                }
            }
        }

        return $this->redirectToRoute('sonata_user_profile_edit');

    }

    public function friendListAction()
    {
        $user = $this->getUser();
        $friends = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship')->getFriends($user);

        return $this->render('@ApplicationSonataUser/Profile/friendlist.html.twig', [
            'friendships'  => $friends
        ]);
    }

    /**
     * @Route("/friendrequests", name="friend_requests")
     */
    public function friendRequestsAction()
    {
        $user           = $this->getUser();
        $entityManager  = $this->container->get('doctrine.orm.entity_manager');
        $friendRequests = $entityManager->getRepository('ApplicationSonataUserBundle:Friendship')->getFriendRequests($user);

        return $this->render('@ApplicationSonataUser/Profile/friendrequests.html.twig', [
            'friendships'   => $friendRequests
        ]);
    }

    /**
     * @Route("/friendlist/delete/{userId}", name="delete_friend")
     */
    public function deleteFriendAction($userId)
    {
        $entityManager = $this->getDoctrine()->getEntityManager();

        $user        = $entityManager->getRepository('ApplicationSonataUserBundle:User')->find($userId);
        $currentUser = $this->getUser();
        if ($user) {
            if ($currentUser->getId() != $userId) {

                $friendship = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship')->isFriend($user, $currentUser);

                if ($friendship) {

                    $entityManager->remove($friendship);
                    $entityManager->flush();
                }
            }
        }
        return $this->redirectToRoute('friends');
    }


    /**
     * @param \Symfony\Component\Form\Form $form
     * @return array
     */
    private function getErrorMessages(\Symfony\Component\Form\Form $form)
    {
        $errors = array();

        foreach ($form->getErrors() as $key => $error) {
            if ($form->isRoot()) {
                $errors['#'][] = $error->getMessage();
            } else {
                $errors[] = $error->getMessage();
            }
        }

        foreach ($form->all() as $child) {
            if (!$child->isValid()) {
                $errors[$child->getName()] = $this->getErrorMessages($child);
            }
        }

        return $errors;
    }

    /**
     * @param $errors
     * @return string
     */
    private function errorMessages($errors)
    {
        $messages = '';

        foreach ($errors as $error) {

            $error = $this->get('translator')->trans($error[0], [], 'SonataUserBundle');

            if   (!is_array($error)) {
                $messages .= "<li>$error</li>";
            } else {
                foreach ($error as $mess) {

                    if (!is_array($mess)) {
                        $messages .= "<li>$mess</li>";

                    } else {
                        foreach ($mess as $m) {
                            $messages .= "<li>$m</li>";
                        }
                    }
                }
            }
        }

        return $messages;
    }
}
