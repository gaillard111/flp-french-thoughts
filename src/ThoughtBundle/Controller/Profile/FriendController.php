<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\Dialog;
use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Form\Type\MessageType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;

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
