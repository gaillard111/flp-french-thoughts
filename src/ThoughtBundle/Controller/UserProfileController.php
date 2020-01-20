<?php

namespace ThoughtBundle\Controller;


use Application\Sonata\UserBundle\Entity\Dialog;
use Application\Sonata\UserBundle\Entity\Friendship;
use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\OptimisticLockException;
use Exception;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use Twig_Error;

class UserProfileController extends Controller
{

    /**
     * @Route("/userslist", name="user_list")
     */
    public function userListAction(Request $request)
    {
        /** @var EntityManager $entityManager */
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        $usersRepository = $entityManager->getRepository(User::class);
        $usersQuery = $usersRepository->createQueryBuilder('u')->select('u')->getQuery();

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $usersQuery,
            $request->query->getInt('page', 1),
            30
        );


        return $this->render('@Thought/usersList.html.twig', [
            'users' =>  $pagination,
        ]);
    }

    /**
     * @Route("/userprofile/{userId}", name="thought_profile")
     * @param Int $userId
     * @return RedirectResponse|Response
     */
    public function showAction($userId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        $user = $this->getUser();
        $possibleFriend = $entityManager->getRepository(User::class)->find($userId);

        if ($user) {
            if ($possibleFriend) {

                $friendship = $entityManager->getRepository(Friendship::class)->isFriend($user, $possibleFriend);
                return $this->render('@ApplicationSonataUser/Thought/userProfile.html.twig', [
                    'user'         =>  $possibleFriend,
                    'friendship'   =>  $friendship
                ]);
            }
        }
        return $this->redirectToRoute('sonata_user_profile_edit');
    }

    /**
     * @Route("/friendrequest/{userId}", name="friend_request")
     * @param Int $userId
     * @return RedirectResponse
     */
    public function friendRequestAction($userId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        $user = $this->getUser();
        $friend = $entityManager->getRepository(User::class)->find($userId);

        if ($user && $friend) {

            $friendship = $entityManager->getRepository(Friendship::class)->isFriend($user, $friend);

            if (!$friendship)   {
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
     * @param Int $requestId
     * @return RedirectResponse
     * @throws OptimisticLockException
     */
    public function acceptRequestAction($requestId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        /** @var Friendship $friendship */
        $friendship = $entityManager->getRepository(Friendship::class)->find($requestId);

        if ($this->getUser() != $friendship->getUser()) {

            if ($friendship) {

                $friendship->setAccepted(true);

                $entityManager->persist($friendship);
                $entityManager->flush();
            }
        }

        return $this->redirectToRoute('friends');
    }

    /**
     * @Route("/newdialog/{userId}", name="new_dialog")
     */
    public function newDialogAction($userId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        /** @var User $user */
        $user = $entityManager->getRepository(User::class)->findOneBy([ 'id' => $userId]);
        /** @var User $curUser */
        $curUser = $this->getUser();

        $friends = $entityManager->getRepository(Friendship::class)->isFriend($user, $curUser);

        if ($friends) {

            if ($user === $curUser) {
                return $this->redirectToRoute('profile');
            }

            $users = [];
            $users[] = $user->getId();
            $users[] = $curUser->getId();


            $dialog = $entityManager->getRepository(Dialog::class)->findUsersDialog($users);

            if (!$user) {
                return $this->redirectToRoute('profile');
            }

            if (!$dialog) {

                /** @var Dialog $dialog */
                $dialog = new Dialog();

                $dialog->addUser($curUser);
                $dialog->addUser($user);

                $curUser->getDialogs()->add($dialog);
                $user->getDialogs()->add($dialog);

                $entityManager->persist($dialog);
                $entityManager->persist($curUser);
                $entityManager->persist($user);
                $entityManager->flush();
            }


            $dialogId = $dialog->getId();


            return $this->redirectToRoute('dialog', [
                'dialogId'  => $dialogId
            ]);
        }

        return $this->redirectToRoute('dialog_list');
    }
}
