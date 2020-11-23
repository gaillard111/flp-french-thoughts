<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\Dialog;
use Application\Sonata\UserBundle\Entity\Friendship;
use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Type\MessageType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use Twig_Error;

/**
 * @Route("/profile")
 */
class FriendController extends Controller
{
    /**
     * @Route("/friends", name="friends")
     */
    public function friendsAction()
    {
        $entityManager  = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship');
        $friendRequests = $entityManager->getCountFriendRequests($this->getUser());
        $friends        = $entityManager->getCountFriends($this->getUser());
        return $this->render('@Thought/Profile/Friends/friends.html.twig', [
            'countReq'     => $friendRequests,
            'countFriends' => $friends,
        ]);
    }

    /**
     * @Route("/dialogs", name="chat_list")
     */
    public function chatList()
    {
        $user = $this->getUser();
        return $this->render('@Thought/Profile/Chat/chat_list.html.twig', []);
    }

    public function friendListAction()
    {
        $user    = $this->getUser();
        $friends = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship')->getFriends($user);

        return $this->render('@Thought/Profile/Friends/friendlist.html.twig', [
            'friendships' => $friends,
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

        return $this->render('@Thought/Profile/Friends/friendrequests.html.twig', [
            'friendships' => $friendRequests,
        ]);
    }


    /**
     * @Route("/friendrequest/{userId}", name="friend_request")
     * @param int $userId
     * @return RedirectResponse
     * @throws Twig_Error
     */
    public function friendRequestAction($userId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        /** @var User $user */
        $user = $this->getUser();
        /** @var User $friend */
        $friend = $entityManager->getRepository(User::class)->find($userId);

        if ($user && $friend) {
            $friendship = $entityManager->getRepository(Friendship::class)->isFriend($user, $friend);

            if (!$friendship) {
                $friendship = new Friendship();
                $friendship->setUser($user);
                $friendship->setFriend($friend);

                $entityManager->persist($friendship);
                $entityManager->flush();

                $mail = $this->get('thought.service.mail_service');
                $mail->friendNotificationMail($user, $friend, $friendship->getId());
            }
        }

        return $this->redirectToRoute('friends');
    }

    /**
     * @Route("/friendrequest/accept/{requestId}", name="accept_friend_request")
     * @param int $requestId
     * @return RedirectResponse
     */
    public function acceptRequestAction($requestId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        /** @var Friendship $friendship */
        $friendship = $entityManager->getRepository(Friendship::class)->find($requestId);

        if ($this->getUser() != $friendship->getUser() && $friendship) {
            $friendship->setAccepted(true);

            $entityManager->persist($friendship);
            $entityManager->flush();
        }

        return $this->redirectToRoute('friends');
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
}
